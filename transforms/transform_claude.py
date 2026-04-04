#!/usr/bin/env python3
"""SpeechButton Transform — pipe text through Claude API.

Usage:  echo "text" | transform_claude.py <prompt_file> [model]

  prompt_file  — text file with the prompt
  model        — default: claude-haiku-4-5-20251001
"""

import sys, json, urllib.request, pathlib, os, time

if len(sys.argv) < 2:
    print("Usage: transform_claude.py <prompt_file> [model]", file=sys.stderr)
    sys.exit(1)

prompt = pathlib.Path(sys.argv[1]).expanduser().read_text().strip()
model = sys.argv[2] if len(sys.argv) > 2 else "claude-haiku-4-5-20251001"
text = sys.stdin.read().strip()
if not text: sys.exit(0)

# Auth: Claude Code OAuth → fallback ANTHROPIC_API_KEY
creds = pathlib.Path.home() / ".claude" / ".credentials.json"
try:
    token = json.loads(creds.read_text())["claudeAiOauth"]["accessToken"]
    headers = {"Authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20"}
except Exception:
    headers = {"x-api-key": os.environ.get("ANTHROPIC_API_KEY", "")}

headers |= {"content-type": "application/json", "anthropic-version": "2023-06-01"}

body = json.dumps({
    "model": model, "max_tokens": 8192,
    "messages": [{"role": "user", "content": f"{prompt}\n\n{text}"}]
}).encode()

# Retry with exponential backoff for 429 rate limit
MAX_RETRIES = 5
for attempt in range(MAX_RETRIES):
    try:
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, headers)
        resp = json.loads(urllib.request.urlopen(req).read())
        print(resp["content"][0]["text"])
        sys.exit(0)
    except urllib.error.HTTPError as e:
        if e.code == 429 and attempt < MAX_RETRIES - 1:
            # Retry-After header or exponential backoff
            wait = float(e.headers.get("retry-after", 2 ** attempt))
            print(f"Rate limited, retry {attempt+1}/{MAX_RETRIES} in {wait:.0f}s...", file=sys.stderr)
            time.sleep(wait)
            continue
        print(f"Transform error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Transform error: {e}", file=sys.stderr)
        sys.exit(1)
