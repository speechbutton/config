#!/usr/bin/env python3
"""Send a message to Slack via Incoming Webhook.

Reads message text from stdin and posts it to a Slack channel
using an Incoming Webhook URL.

Usage:
    echo "Hello team" | send_slack.py
    echo "Hello team" | send_slack.py --url https://hooks.slack.com/services/T.../B.../xxx

Configuration:
    SLACK_WEBHOOK_URL environment variable (required)
    Or inline in exec: SLACK_WEBHOOK_URL=https://hooks.slack.com/... integrations/send_slack.py

Setup:
    1. Go to https://api.slack.com/apps → Create New App
    2. Features → Incoming Webhooks → Activate
    3. Add New Webhook to Workspace → select channel
    4. Copy the Webhook URL
"""

import json
import os
import sys
import urllib.request


def get_webhook_url() -> str:
    """Get Slack Webhook URL from --url flag or environment."""
    if "--url" in sys.argv:
        return sys.argv[sys.argv.index("--url") + 1]

    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print(
            "SLACK_WEBHOOK_URL not set.\n"
            "Get one at https://api.slack.com/apps → Incoming Webhooks",
            file=sys.stderr,
        )
        sys.exit(1)
    return url


def send_message(webhook_url: str, text: str) -> int:
    """Post a message to Slack. Returns HTTP status code."""
    payload = json.dumps({"text": text}).encode()

    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    resp = urllib.request.urlopen(req, timeout=10)
    return resp.status


def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    webhook_url = get_webhook_url()

    try:
        status = send_message(webhook_url, text)
        preview = text[:60].replace("\n", " ")
        print(f"Slack ({status}): {preview}...")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"Slack error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
