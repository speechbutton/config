#!/usr/bin/env python3
"""Append text to an Obsidian vault file. 100% local — no API calls.

Reads text from stdin and appends it to a markdown file in your
Obsidian vault. Creates the file if it doesn't exist.

Usage:
    echo "Quick thought" | send_obsidian.py
    echo "Meeting notes" | send_obsidian.py --file "meetings/2026-04-04.md"
    echo "Journal entry" | send_obsidian.py --daily

Configuration:
    OBSIDIAN_VAULT — Path to vault (required)
    Or --vault /path/to/vault flag

Modes:
    --daily     Append to daily note: YYYY-MM-DD.md (default)
    --file X    Append to specific file
    --inbox     Append to inbox.md
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def get_vault_path() -> Path:
    """Get Obsidian vault path."""
    if "--vault" in sys.argv:
        return Path(sys.argv[sys.argv.index("--vault") + 1]).expanduser()

    vault = os.environ.get("OBSIDIAN_VAULT")
    if vault:
        return Path(vault).expanduser()

    # Common locations
    for candidate in [
        Path.home() / "Documents" / "Obsidian",
        Path.home() / "Obsidian",
        Path.home() / "vault",
    ]:
        if candidate.exists():
            return candidate

    print(
        "OBSIDIAN_VAULT not set. Set env var or use --vault /path/to/vault",
        file=sys.stderr,
    )
    sys.exit(1)


def get_target_file(vault: Path) -> Path:
    """Determine target file based on flags."""
    if "--file" in sys.argv:
        filename = sys.argv[sys.argv.index("--file") + 1]
        return vault / filename

    if "--inbox" in sys.argv:
        return vault / "inbox.md"

    # Default: daily note
    today = datetime.now().strftime("%Y-%m-%d")
    return vault / f"{today}.md"


def main():
    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    vault = get_vault_path()
    target = get_target_file(vault)

    # Create parent directories if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    # Add timestamp header
    timestamp = datetime.now().strftime("%H:%M")

    # Append to file
    separator = "\n\n---\n\n" if target.exists() and target.stat().st_size > 0 else ""
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"{separator}**{timestamp}** — {text}\n")

    filename = target.relative_to(vault)
    print(f"Obsidian: → {filename}")


if __name__ == "__main__":
    main()
