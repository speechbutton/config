# SpeechButton Configuration Template

Default configuration files for [SpeechButton](https://speechbutton.com) — macOS voice-to-text app.

## Installation

```bash
# First install (creates ~/.config/speechbutton/)
curl -sL https://github.com/pvtrn/speechbutton-config/archive/main.tar.gz | tar xz -C /tmp
cp -rn /tmp/speechbutton-config-main/* ~/.config/speechbutton/
rm -rf /tmp/speechbutton-config-main
```

Or clone:
```bash
git clone https://github.com/pvtrn/speechbutton-config ~/.config/speechbutton
```

## Files

| File | Description |
|------|-------------|
| `config.toml` | Main configuration — hotkeys, output routing, models |
| `scripts/transform_claude.py` | Claude API transform (uses Claude Code OAuth) |
| `scripts/transform_openai.py` | OpenAI API transform (uses Codex OAuth or API key) |
| `prompts/default.md` | Default cleanup prompt |
| `prompts/translate_en.md` | Translate to English prompt |
| `prompts/cleanup.md` | Grammar cleanup prompt |
| `CLAUDE.md` | AI agent configuration guide |

## Updating

```bash
cd ~/.config/speechbutton
git pull
```

Or manually download updated files from this repository.
