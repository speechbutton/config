#!/usr/bin/env python3
"""SpeechButton Transform — pipe text through OpenAI API.

Usage:  echo "text" | transform_openai.py <prompt_file> [model]

  prompt_file  — text file with the prompt
  model        — default: gpt-4o-mini

Auth priority:
  1. Codex CLI OAuth (~/.codex/auth.json) — uses ChatGPT subscription, no extra API key needed
  2. OPENAI_API_KEY env var — standard API key from platform.openai.com
"""

import sys, json, urllib.request, pathlib, os


def refresh_codex_token():
    """Refresh OAuth token from Codex CLI credentials."""
    auth_path = pathlib.Path.home() / ".codex" / "auth.json"
    try:
        auth = json.loads(auth_path.read_text())
        refresh = auth.get("tokens", {}).get("refresh_token")
        if not refresh:
            return auth.get("tokens", {}).get("access_token")

        body = json.dumps({
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": "app_EMoamEEZ73f0CkXaXp7hrann"
        }).encode()
        req = urllib.request.Request(
            "https://auth.openai.com/oauth/token", body,
            {"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return resp.get("access_token")
    except Exception:
        return None


def call_responses_api(token, model, prompt, text):
    """Call OpenAI Responses API (same as Codex CLI uses)."""
    body = json.dumps({
        "model": model,
        "input": [
            {"role": "developer", "content": prompt},
            {"role": "user", "content": text},
        ],
    }).encode()

    req = urllib.request.Request("https://api.openai.com/v1/responses", body, {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "x-responses",
    })
    resp = json.loads(urllib.request.urlopen(req).read())

    # Extract text from Responses API output
    for item in resp.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
    return ""


def call_chat_completions_api(token, model, prompt, text):
    """Call OpenAI Chat Completions API (standard API key)."""
    body = json.dumps({
        "model": model,
        "max_tokens": 8192,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]
    }).encode()

    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", body, {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp["choices"][0]["message"]["content"]


# ── Main ──────────────────────────────────────────────

if len(sys.argv) < 2:
    print("Usage: transform_openai.py <prompt_file> [model]", file=sys.stderr)
    sys.exit(1)

prompt = pathlib.Path(sys.argv[1]).expanduser().read_text().strip()
model = sys.argv[2] if len(sys.argv) > 2 else "gpt-4o-mini"
text = sys.stdin.read().strip()
if not text:
    sys.exit(0)

# Try Codex OAuth first (Responses API)
codex_token = refresh_codex_token()
if codex_token:
    try:
        result = call_responses_api(codex_token, model, prompt, text)
        if result:
            print(result)
            sys.exit(0)
    except urllib.error.HTTPError as e:
        # 400 = model not supported by Responses API, try Chat Completions
        if e.code != 400:
            print(f"Transform error: {e} (model={model})", file=sys.stderr)
            sys.exit(1)
        # Fall through to Chat Completions with same token
        try:
            result = call_chat_completions_api(codex_token, model, prompt, text)
            if result:
                print(result)
                sys.exit(0)
        except Exception as e2:
            print(f"Transform error: {e2} (model={model})", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Transform error: {e} (model={model})", file=sys.stderr)
        sys.exit(1)

# Fallback: OPENAI_API_KEY (Chat Completions API)
api_key = os.environ.get("OPENAI_API_KEY", "")
if api_key:
    try:
        result = call_chat_completions_api(api_key, model, prompt, text)
        if result:
            print(result)
            sys.exit(0)
    except Exception as e:
        print(f"Transform error: {e} (model={model})", file=sys.stderr)
        sys.exit(1)

print(f"Transform error: no OpenAI credentials found (model={model})", file=sys.stderr)
sys.exit(1)
