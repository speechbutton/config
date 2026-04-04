#!/usr/bin/env python3
"""Create a GitHub issue from stdin JSON.

Reads a JSON object with title, body, and labels from stdin
and creates an issue via the GitHub REST API.

Usage:
    echo '{"title":"Bug","body":"Details"}' | send_github.py
    echo '{"title":"Bug","body":"Details"}' | send_github.py --repo owner/repo

Configuration:
    GITHUB_TOKEN — Personal access token (required)
        Get one at https://github.com/settings/tokens → Fine-grained → Issues: Read & Write
    GITHUB_REPO — Repository in "owner/repo" format (required, or use --repo flag)
"""

import json
import os
import sys
import urllib.request


API_URL = "https://api.github.com/repos/{repo}/issues"


def get_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "GITHUB_TOKEN not set.\n"
            "Get one at https://github.com/settings/tokens",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def get_repo() -> str:
    """Get repo from --repo flag or environment."""
    if "--repo" in sys.argv:
        return sys.argv[sys.argv.index("--repo") + 1]

    repo = os.environ.get("GITHUB_REPO")
    if not repo:
        print(
            "GITHUB_REPO not set. Use --repo owner/repo or set env var.",
            file=sys.stderr,
        )
        sys.exit(1)
    return repo


def create_issue(token: str, repo: str, title: str, body: str, labels: list) -> dict:
    """Create a GitHub issue via REST API."""
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    req = urllib.request.Request(
        API_URL.format(repo=repo),
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())


def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.strip().split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    # Parse JSON input
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"title": text[:80], "body": text, "labels": []}

    title = data.get("title", "Untitled")
    body = data.get("body", "")
    labels = data.get("labels", [])

    token = get_token()
    repo = get_repo()

    try:
        result = create_issue(token, repo, title, body, labels)
        number = result.get("number", "?")
        url = result.get("html_url", "")
        print(f"Created #{number}: {title[:50]}")
        if url:
            print(url, file=sys.stderr)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:200]
        print(f"GitHub error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
