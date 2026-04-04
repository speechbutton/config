#!/usr/bin/env python3
"""Create a Linear issue from stdin JSON.

Reads a JSON object with title, description, and priority from stdin
(output of transform_claude.py with linear_issue.md prompt) and creates
an issue in Linear via GraphQL API.

Usage:
    echo '{"title":"Bug","description":"Details","priority":2}' | send_linear.py
    echo '{"title":"Bug","description":"Details"}' | send_linear.py --team "Engineering"

Configuration:
    LINEAR_API_KEY environment variable (required)

Team resolution:
    1. --team flag (team name, matched against Linear teams)
    2. First team in the workspace (auto-detect)
"""

import json
import os
import sys
import urllib.request


API_URL = "https://api.linear.app/graphql"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """Get Linear API key from environment."""
    key = os.environ.get("LINEAR_API_KEY")
    if not key:
        print("LINEAR_API_KEY not set. Get one at https://linear.app/settings/account/security", file=sys.stderr)
        sys.exit(1)
    return key


# ---------------------------------------------------------------------------
# GraphQL helpers
# ---------------------------------------------------------------------------

def graphql(api_key: str, query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against Linear API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
    )

    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())

    if "errors" in result:
        print(f"Linear API error: {result['errors']}", file=sys.stderr)
        sys.exit(1)

    return result.get("data", {})


def resolve_team_id(api_key: str) -> str:
    """Resolve the team ID from --team flag, config, or auto-detect."""
    # Check --team flag
    team_name = None
    if "--team" in sys.argv:
        team_name = sys.argv[sys.argv.index("--team") + 1]

    # Fetch teams
    data = graphql(api_key, "query { teams { nodes { id name } } }")
    teams = data.get("teams", {}).get("nodes", [])

    if not teams:
        print("No teams found in Linear workspace.", file=sys.stderr)
        sys.exit(1)

    # Match by name
    if team_name:
        for t in teams:
            if t["name"].lower() == team_name.lower():
                return t["id"]
        print(f"Team '{team_name}' not found. Available: {', '.join(t['name'] for t in teams)}", file=sys.stderr)
        sys.exit(1)

    # Auto-detect: first team
    return teams[0]["id"]


def create_issue(api_key: str, team_id: str, title: str, description: str, priority: int) -> dict:
    """Create a Linear issue and return the issue data."""
    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                identifier
                title
                url
            }
        }
    }
    """

    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
    }

    data = graphql(api_key, mutation, variables)
    result = data.get("issueCreate", {})

    if not result.get("success"):
        print("Failed to create issue.", file=sys.stderr)
        sys.exit(1)

    return result.get("issue", {})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    # Strip markdown code fences if present (Claude sometimes wraps JSON in ```json ... ```)
    if text.startswith("```"):
        lines = text.strip().split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    # Parse JSON input (from transform_claude.py + linear_issue.md)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Plain text fallback — use as title
        data = {"title": text[:80], "description": text, "priority": 3}

    title = data.get("title", "Untitled")
    description = data.get("description", "")
    priority = data.get("priority", 3)

    api_key = get_api_key()
    team_id = resolve_team_id(api_key)
    issue = create_issue(api_key, team_id, title, description, priority)

    identifier = issue.get("identifier", "?")
    url = issue.get("url", "")
    print(f"Created {identifier}: {title[:50]}{'…' if len(title) > 50 else ''}")
    if url:
        print(url, file=sys.stderr)


if __name__ == "__main__":
    main()
