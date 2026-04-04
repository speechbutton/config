#!/usr/bin/env python3
"""Create a Notion page from stdin text.

Reads text from stdin and creates a new page in a Notion database
or appends to an existing page via the Notion API.

Usage:
    echo "Meeting notes..." | send_notion.py
    echo "Meeting notes..." | send_notion.py --database "Tasks"

Configuration:
    NOTION_API_KEY — Integration token from https://www.notion.so/my-integrations
    NOTION_PAGE_ID — Parent page ID (append blocks to existing page)
    Or NOTION_DATABASE_ID — Database ID (create new page in database)
"""

import json
import os
import sys
import urllib.request
from datetime import datetime


API_URL = "https://api.notion.com/v1"


def get_api_key() -> str:
    """Get Notion API key from environment."""
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        print(
            "NOTION_API_KEY not set.\n"
            "Get one at https://www.notion.so/my-integrations",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def notion_request(api_key: str, method: str, path: str, body: dict = None) -> dict:
    """Make a Notion API request."""
    url = f"{API_URL}{path}"
    data = json.dumps(body).encode() if body else None

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
    )

    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())


def text_to_blocks(text: str) -> list:
    """Convert plain text to Notion block objects."""
    blocks = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # Heading detection
        if paragraph.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": paragraph[2:]}}]},
            })
        elif paragraph.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": paragraph[3:]}}]},
            })
        elif paragraph.startswith("- ") or paragraph.startswith("• "):
            for line in paragraph.split("\n"):
                item = line.lstrip("-•").strip()
                if item:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": item}}]},
                    })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": paragraph}}]},
            })
    return blocks


def append_to_page(api_key: str, page_id: str, text: str) -> str:
    """Append blocks to an existing Notion page."""
    blocks = text_to_blocks(text)
    result = notion_request(api_key, "PATCH", f"/blocks/{page_id}/children", {"children": blocks})
    return page_id


def create_page(api_key: str, database_id: str, title: str, text: str) -> str:
    """Create a new page in a Notion database."""
    blocks = text_to_blocks(text)
    body = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
        },
        "children": blocks,
    }
    result = notion_request(api_key, "POST", "/pages", body)
    return result.get("url", result.get("id", "?"))


def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    api_key = get_api_key()
    page_id = os.environ.get("NOTION_PAGE_ID")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    try:
        if page_id:
            append_to_page(api_key, page_id, text)
            print(f"Notion: appended to page")
        elif database_id:
            title = text.split("\n")[0][:80]
            url = create_page(api_key, database_id, title, text)
            print(f"Notion: {url}")
        else:
            print(
                "Set NOTION_PAGE_ID (append to page) or NOTION_DATABASE_ID (create new page)",
                file=sys.stderr,
            )
            sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"Notion error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
