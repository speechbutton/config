#!/usr/bin/env python3
"""SpeechButton Transform — local LLM via llama-server (Gemma 4).

Usage:  echo "text" | transform_local.py <prompt_file> [model]

No API keys needed. Runs entirely on device at ~94 tokens/sec.
Requires: llama-server running with a GGUF model.

Start server:
  llama-server -m ~/.config/speechbutton/models/gemma-4-e2b-it-Q8_0.gguf -ngl 99 --port 8234
"""

import sys, json, urllib.request, pathlib

if len(sys.argv) < 2:
    print("Usage: transform_local.py <prompt_file>", file=sys.stderr)
    sys.exit(1)

prompt = pathlib.Path(sys.argv[1]).expanduser().read_text().strip()
text = sys.stdin.read().strip()
if not text:
    sys.exit(0)

SERVER_URL = "http://localhost:8234/v1/chat/completions"

body = json.dumps({
    "messages": [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text},
    ],
    "temperature": 0.1,
    "max_tokens": 512,
}).encode()

try:
    req = urllib.request.Request(SERVER_URL, body, {"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    print(resp["choices"][0]["message"]["content"].strip())
except Exception as e:
    print(f"Transform error: {e}", file=sys.stderr)
    print("Make sure llama-server is running: llama-server -m model.gguf -ngl 99 --port 8234", file=sys.stderr)
    sys.exit(1)
