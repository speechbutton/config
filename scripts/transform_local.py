#!/usr/bin/env python3
"""SpeechButton Transform — local LLM via Ollama or llama-server.

Usage:  echo "text" | transform_local.py <prompt_file> [model]

  prompt_file  — text file with the system prompt
  model        — Ollama model name (default: gemma4-e2b) or path to GGUF file

No API keys needed. Runs entirely on device.
Requires one of:
  - Ollama: brew install ollama && ollama serve
  - llama-server: brew install llama.cpp && llama-server -m model.gguf
"""

import sys, json, urllib.request, pathlib

if len(sys.argv) < 2:
    print("Usage: transform_local.py <prompt_file> [model]", file=sys.stderr)
    sys.exit(1)

prompt = pathlib.Path(sys.argv[1]).expanduser().read_text().strip()
model = sys.argv[2] if len(sys.argv) > 2 else "gemma4-e2b"
text = sys.stdin.read().strip()
if not text:
    sys.exit(0)


def try_ollama():
    """Try Ollama API (localhost:11434)."""
    body = json.dumps({
        "model": model,
        "prompt": f"{prompt}\n\n{text}",
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate", body,
        {"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return resp.get("response", "").strip()


def try_llama_server():
    """Try llama-server API (localhost:8080)."""
    body = json.dumps({
        "prompt": f"{prompt}\n\n{text}",
        "n_predict": 256,
        "temperature": 0.1,
        "stop": ["<end_of_turn>", "<eos>", "\n\n"],
    }).encode()
    req = urllib.request.Request(
        "http://localhost:8080/completion", body,
        {"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return resp.get("content", "").strip()


# Try Ollama first, then llama-server
for fn, name in [(try_ollama, "Ollama"), (try_llama_server, "llama-server")]:
    try:
        result = fn()
        if result:
            print(result)
            sys.exit(0)
    except Exception:
        continue

print("Transform error: no local LLM server found (install Ollama or llama-server)", file=sys.stderr)
sys.exit(1)
