#!/usr/bin/env python3
"""Send a message to Telegram via Bot API.

Reads message text from stdin and sends it to a Telegram chat
using the Bot API.

Usage:
    echo "Hello" | send_telegram.py
    echo "Hello" | send_telegram.py --chat 123456789

Configuration:
    TELEGRAM_BOT_TOKEN — Bot token from @BotFather (required)
    TELEGRAM_CHAT_ID — Chat/group/channel ID (required, or use --chat flag)

Setup:
    1. Message @BotFather on Telegram → /newbot → get token
    2. Send a message to your bot, then get chat_id:
       curl https://api.telegram.org/bot<TOKEN>/getUpdates | jq '.result[0].message.chat.id'
    3. Set env vars or use inline in config.toml exec
"""

import json
import os
import sys
import urllib.request


API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def get_bot_token() -> str:
    """Get Telegram Bot token from environment."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print(
            "TELEGRAM_BOT_TOKEN not set.\n"
            "Get one from @BotFather on Telegram: /newbot",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def get_chat_id() -> str:
    """Get Telegram chat ID from --chat flag or environment."""
    if "--chat" in sys.argv:
        return sys.argv[sys.argv.index("--chat") + 1]

    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        print(
            "TELEGRAM_CHAT_ID not set.\n"
            "Get it: curl https://api.telegram.org/bot<TOKEN>/getUpdates",
            file=sys.stderr,
        )
        sys.exit(1)
    return chat_id


def send_message(token: str, chat_id: str, text: str) -> dict:
    """Send a message via Telegram Bot API."""
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()

    req = urllib.request.Request(
        API_URL.format(token=token),
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    token = get_bot_token()
    chat_id = get_chat_id()

    try:
        result = send_message(token, chat_id, text)
        if result.get("ok"):
            preview = text[:60].replace("\n", " ")
            print(f"Telegram: {preview}...")
        else:
            print(f"Telegram error: {result}", file=sys.stderr)
            sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"Telegram error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
