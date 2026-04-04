# SpeechButton — AI Agent Configuration Guide

## What is SpeechButton?
A macOS menu bar app that transcribes speech to text. Hold a hotkey, speak, release — text appears instantly.

## Config location
`~/.config/speechbutton/config.toml`

This is a symlink to the app's sandbox container (created automatically on first launch).
All relative paths in this document are relative to `~/.config/speechbutton/`.
Transform scripts and exec commands run with this folder as working directory.

## What you can configure

### Hotkeys & Channels
The first `[[hotkey]]` without a `channel` is the default — it works when you just hold the key and speak.
Channels are **optional** — you can have just one default hotkey and no channels at all.
If you add channels, they activate when you press a channel key (1-9, a-z) while holding the main key.

Each `[[hotkey]]` defines a key binding with its own output routing:
```toml
[[hotkey]]
key = "RightCommand"     # Modifier key to hold (RightCommand, LeftShift, etc.)
channel = "1"            # Channel key (press while holding key), omit for default
name = "my-channel"      # Display name
paste = "accessibility"  # Output: "accessibility" (paste at cursor), "clipboard", or "false"
file = "~/notes.txt"     # Output: append to file
webhook = "http://..."   # Output: HTTP POST with JSON payload
exec = "my_script.py"    # Output: pipe text to shell command via stdin
transform = "..."        # Pre-process text through command before output
output_format = "text"   # "text" or "json"
```

### Output types (choose ONE per hotkey)

**Paste** — inserts text where the cursor is (via Cmd+V simulation):
```toml
paste = "accessibility"  # or "clipboard" (copy only, user pastes manually)
```

**File** — appends each transcription as a new line:
```toml
file = "~/notes.txt"
# output_format = "json"  # optional: write JSON instead of plain text
```

**Webhook** — sends HTTP POST:
```toml
webhook = "http://localhost:8080/transcription"
```

**Exec** — pipes text to a shell command via stdin:
```toml
exec = "integrations/send_slack.py"
```
The command receives the transcribed text on stdin (plain text by default).
Set `output_format = "json"` to receive JSON instead.

### JSON format
When `output_format = "json"` or for webhook, the JSON structure is:

```json
{
  "text": "Hello, this is a test.",
  "lang": "en",
  "model": "parakeet-tdt-0.6b-v3-int8",
  "duration_ms": 3200,
  "source": "ptt",
  "device": "MacBook Pro Microphone",
  "timestamp": "2026-04-01T12:00:00.000Z"
}
```

Webhook adds `"event": "transcription"` to the payload.

Fields:
- `text` — full transcribed text (after hallucination filter + auto-punctuation + transform)
- `lang` — detected language code
- `model` — STT model used
- `duration_ms` — audio duration in milliseconds
- `source` — "ptt" (push-to-talk) or "vad" (voice activity detection)
- `device` — input device name
- `timestamp` — ISO 8601 UTC

Note: for exec/webhook/file, audio is always accumulated fully before transcription — no intermediate chunks. Chunks are only used for paste-at-cursor mode.

Examples for exec:
- `pbcopy` — copy to clipboard
- `integrations/send_email.py` — custom script (relative path)
- `curl -X POST -d @- http://api.example.com/messages` — HTTP POST

### Transform (optional pre-processing)
Runs BEFORE output. Text is piped through the command (stdin → stdout).
If transform fails (exit code ≠ 0), output is cancelled.

**Working directory is the config folder**, so use relative paths:

```toml
# Via Claude API (uses your Claude Code subscription):
transform = "transforms/transform_claude.py prompts/translate_en.md"

# Via OpenAI API (uses your Codex subscription):
transform = "transforms/transform_openai.py prompts/cleanup.md gpt-4o-mini"

# Custom script (absolute paths also work):
transform = "python3 ~/my_transform.py"
```

Prompt files are in `prompts/` directory as `.md` files. Examples included:
- `translate_en.md` — translate to English
- `cleanup.md` — remove filler words, fix grammar

### Example configurations

**Default — paste at cursor:**
```toml
[[hotkey]]
key = "RightCommand"
name = "default"
```

**Channel 1 — translate and paste:**
```toml
[[hotkey]]
key = "RightCommand"
channel = "1"
name = "translate"
transform = "transforms/transform_claude.py prompts/translate_en.md"
```

**Channel 2 — append to notes file:**
```toml
[[hotkey]]
key = "RightCommand"
channel = "2"
name = "notes"
file = "~/Documents/voice-notes.txt"
```

**Channel 3 — send to Slack:**
```toml
[[hotkey]]
key = "RightCommand"
channel = "3"
name = "slack"
exec = "integrations/send_slack.py"
```

**Channel 4 — webhook to API:**
```toml
[[hotkey]]
key = "RightCommand"
channel = "4"
name = "api"
webhook = "http://localhost:8080/voice"
output_format = "json"
```

**Channel 5 — clean up and send to Claude Code agent:**
```toml
[[hotkey]]
key = "RightCommand"
channel = "5"
name = "claude-agent"
transform = "transforms/transform_claude.py prompts/cleanup.md"
exec = "claude -p --bare"
```

### Speech Recognition
```toml
model = "parakeet-tdt-0.6b-v3-int8"  # Fast, 25+ languages, low hallucinations
# model = "ggml-large-v3-turbo-q5_0.bin"  # Whisper: 100+ languages, slower
language = "auto"                      # or specific: "en", "ru", "de", etc.
auto_punctuation = true
```

### Voice Activity Detection (VAD)
Hands-free mode — automatically detects when you speak:
```toml
[vad]
enabled = false
chunk_silence_sec = 0.55  # Silence duration to end a speech segment
```

### Push-to-Talk Chunking
Splits long recordings at silence gaps during hold:
```toml
[ptt]
chunking_enabled = true
chunk_silence_sec = 1.0   # Silence duration to split a chunk
```

### Auto-Send
Automatically presses Enter after pasting (for chat apps):
```toml
auto_send = false
send_delay_sec = 3.0
```

### Input Device
```toml
input_device = ""  # Empty = system default, or exact device name like "iPhone (Pavel) Microphone"
```

### Device Rules
```toml
[[device_rule]]
match = "iPhone"       # Substring match (case-insensitive)
keep_hot = true        # Keep audio stream always running for this device
```

### Advanced
```toml
[advanced]
audio_backend = "auto"       # "auto" (VPIO on macOS 15+), "vpio", "hal"
max_recording_sec = 300      # Safety limit
keep_audio_hot = false       # Keep mic stream always running (faster start)
```

### Hallucination Filtering
Per-model word lists in the config folder (one phrase per line, case-insensitive):
- `hallucinations_parakeet`
- `hallucinations_whisper`

### Writing prompts

Prompt files are plain `.md` files in the `prompts/` directory.
The entire file content is sent as the system prompt to the AI model.
The transcribed speech is appended as the user message.

Example prompt (`prompts/my_prompt.md`):
```
You are a helpful assistant. The user will give you raw speech transcription.
Clean it up: fix grammar, remove filler words, make it professional.
Return ONLY the cleaned text, nothing else. Do not add explanations.
```

Key rules for prompts:
- End with "Return ONLY the result, nothing else" to prevent extra commentary
- Keep prompts focused on one task
- The AI receives: `{prompt}\n\n{transcribed_text}`

### Transform pipeline flow

```
Audio → Transcribe → [Transform] → Output
                         ↓
                 stdin: raw text
                 stdout: transformed text
                 exit 0: success → output
                 exit ≠ 0: abort (no output)
```

Transform command receives text on **stdin** and must print result to **stdout**.
Any command that reads stdin and writes stdout works — not just the built-in scripts.

Example custom transform:
```bash
#!/bin/bash
# transforms/uppercase.sh
tr '[:lower:]' '[:upper:]'
```

### Available hotkey names

| Key name | Key |
|----------|-----|
| `RightCommand` | Right ⌘ |
| `LeftCommand` | Left ⌘ |
| `RightShift` | Right ⇧ |
| `LeftShift` | Left ⇧ |
| `RightOption` | Right ⌥ |
| `LeftOption` | Left ⌥ |
| `RightControl` | Right ⌃ |
| `LeftControl` | Left ⌃ |
| `CapsLock` | ⇪ |

### Diagnostics

Check transform errors:
```bash
# Open config folder
open ~/.config/speechbutton

# View logs
tail -f ~/.config/speechbutton/logs/speechbutton.log | grep -i transform
```

Test a transform manually:
```bash
cd ~/.config/speechbutton
echo "test input text" | python3 transforms/transform_claude.py prompts/translate_en.md
```

Config is hot-reloaded — changes take effect immediately, no restart needed.

### Scripts directory
`transforms/` — transform scripts (text processing)
`integrations/` — exec scripts (send to external services)
Built-in:
- `transform_claude.py` — Claude API transform (uses Claude Code OAuth)
- `transform_openai.py` — OpenAI API transform (uses Codex OAuth or OPENAI_API_KEY)
