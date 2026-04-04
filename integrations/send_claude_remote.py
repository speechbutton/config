#!/usr/bin/env python3
"""Send text to a Claude Code Remote Control session via Anthropic API.

Reads text from stdin and pushes it as a user message into an active
Remote Control session. The session keeps running locally on your machine;
this script just relays messages through the Anthropic API.

Usage:
    echo "Fix the auth bug" | send_claude_remote.py <session_id>
    echo "Fix the auth bug" | send_claude_remote.py                # auto-detect

Session ID resolution (first match wins):
    1. CLI argument
    2. CLAUDE_RC_SESSION environment variable
    3. Auto-detect from most recent bridge-pointer.json in ~/.claude/projects/

Authentication:
    OAuth token from ~/.claude/.credentials.json (Claude Code login).
    The Sessions API requires OAuth — API keys are not supported.
    Both machines (sender and RC host) must be logged into the same claude.ai account.
"""

import json
import os
import pathlib
import sys
import urllib.request
import uuid


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def get_oauth_token() -> str:
    """Read the OAuth access token from Claude Code credentials file."""
    creds_path = pathlib.Path.home() / ".claude" / ".credentials.json"
    if not creds_path.exists():
        print("No credentials found. Run 'claude' and use /login first.", file=sys.stderr)
        sys.exit(1)

    creds = json.loads(creds_path.read_text())
    return creds["claudeAiOauth"]["accessToken"]


def get_org_uuid(token: str) -> str:
    """Fetch the organization UUID for the authenticated user."""
    req = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp["organization"]["uuid"]


# ---------------------------------------------------------------------------
# Session discovery
# ---------------------------------------------------------------------------

def find_session_id() -> str | None:
    """Auto-detect the most recently active Remote Control session.

    Scans ~/.claude/projects/ for bridge-pointer.json files (written by
    Claude Code when a Remote Control session starts) and returns the
    session ID from the most recently modified one.
    """
    claude_dir = pathlib.Path.home() / ".claude" / "projects"
    if not claude_dir.exists():
        return None

    pointers = sorted(
        claude_dir.rglob("bridge-pointer.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for pointer in pointers:
        try:
            data = json.loads(pointer.read_text())
            session_id = data.get("sessionId") or data.get("session_id")
            if session_id:
                return session_id
        except Exception:
            continue

    return None


def resolve_session_id() -> str:
    """Resolve session ID from CLI arg, env var, or auto-detection."""
    # 1. CLI argument
    if len(sys.argv) > 1:
        return sys.argv[1]

    # 2. Environment variable
    env_session = os.environ.get("CLAUDE_RC_SESSION")
    if env_session:
        return env_session

    # 3. Auto-detect from bridge-pointer.json
    detected = find_session_id()
    if detected:
        return detected

    print(
        "No session ID found.\n"
        "  Pass as argument:  send_claude_remote.py <session_id>\n"
        "  Or set env var:    export CLAUDE_RC_SESSION=session_xxx\n"
        "  Or start RC:       claude remote-control",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def send_message(session_id: str, text: str, token: str, org_uuid: str) -> int:
    """Send a user message to a Remote Control session.

    Uses POST /v1/sessions/{session_id}/events — the same endpoint
    that claude.ai/code and the Claude mobile app use internally.

    Returns the HTTP status code (200 = success).
    """
    payload = {
        "events": [{
            "uuid": str(uuid.uuid4()),
            "session_id": session_id,
            "type": "user",
            "parent_tool_use_id": None,
            "message": {
                "role": "user",
                "content": text,
            },
        }]
    }

    req = urllib.request.Request(
        f"https://api.anthropic.com/v1/sessions/{session_id}/events",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "ccr-byoc-2025-07-29",
            "x-organization-uuid": org_uuid,
        },
    )

    resp = urllib.request.urlopen(req, timeout=30)
    return resp.status


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    session_id = resolve_session_id()
    token = get_oauth_token()
    org_uuid = get_org_uuid(token)

    try:
        status = send_message(session_id, text, token, org_uuid)
        preview = text[:60].replace("\n", " ")
        print(f"Sent to RC ({status}): {preview}...")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
