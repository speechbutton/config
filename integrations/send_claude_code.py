#!/usr/bin/env python3
"""Send text to Claude Code CLI as a one-shot prompt.

Reads a task from stdin and passes it to `claude --print --bare -p`,
which runs Claude Code non-interactively and prints the result.

Usage:
    echo "Fix the bug in auth.py" | send_claude_code.py
    echo "Fix the bug in auth.py" | send_claude_code.py --cwd /path/to/project
"""

import os
import shutil
import subprocess
import sys


def find_claude_binary() -> str:
    """Locate the claude CLI binary."""
    # Check PATH first
    found = shutil.which("claude")
    if found:
        return found

    # Common install locations
    candidates = [
        os.path.expanduser("~/.local/bin/claude"),
        "/opt/homebrew/bin/claude",
        "/usr/local/bin/claude",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    print("claude CLI not found in PATH or common locations.", file=sys.stderr)
    sys.exit(1)


def parse_cwd() -> str | None:
    """Extract --cwd argument if provided."""
    if "--cwd" in sys.argv:
        idx = sys.argv.index("--cwd")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None


def main():
    task = sys.stdin.read().strip()
    if not task:
        sys.exit(0)

    claude = find_claude_binary()
    cwd = parse_cwd()

    try:
        result = subprocess.run(
            [claude, "--print", "--bare", "-p", task],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            # Show first line of response as confirmation
            response = result.stdout.strip()
            first_line = response.split("\n")[0][:100] if response else "Done"
            print(f"Claude: {first_line}")
        else:
            print(f"Claude error: {result.stderr[:100]}", file=sys.stderr)
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print("Claude timeout (120s)", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
