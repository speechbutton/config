#!/usr/bin/env python3
"""Tests for transform_claude.py and transform_openai.py

Run: python3 test_transforms.py
Requires: valid credentials (~/.claude/.credentials.json and/or ~/.codex/auth.json)
"""

import subprocess
import sys
import os
import tempfile
import pathlib

SCRIPTS_DIR = pathlib.Path(__file__).parent
PROMPTS_DIR = SCRIPTS_DIR.parent / "prompts"

passed = 0
failed = 0


def run_transform(script, prompt_file, text, model=None, timeout=30):
    """Run a transform script and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script), str(prompt_file)]
    if model:
        cmd.append(model)
    result = subprocess.run(
        cmd, input=text, capture_output=True, text=True, timeout=timeout
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


# ============================================================
# Setup: create temp prompt file
# ============================================================

with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
    f.write("Translate the following text to English.\nReturn ONLY the translation, nothing else.")
    translate_prompt = f.name

with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
    f.write("Return the input text unchanged.")
    echo_prompt = f.name


# ============================================================
print("\n═══════════════════════════════════════════")
print("TRANSFORM_CLAUDE.PY")
print("═══════════════════════════════════════════")
# ============================================================

has_claude = pathlib.Path.home().joinpath(".claude/.credentials.json").exists()

if not has_claude:
    print("  ⚠ Skipping Claude tests — no credentials found")
else:
    # Test 1: Basic transform works
    print("\n--- Basic functionality ---")
    code, out, err = run_transform("transform_claude.py", echo_prompt, "Hello world")
    test("Claude returns text", code == 0 and len(out) > 0, f"code={code} err={err}")

    # Test 2: Empty input → exit 0, no output
    code, out, err = run_transform("transform_claude.py", echo_prompt, "")
    test("Empty input exits cleanly", code == 0 and out == "", f"code={code} out={out}")

    # Test 3: Translation works
    code, out, err = run_transform("transform_claude.py", translate_prompt, "Привет мир")
    test("Russian→English translation", code == 0 and len(out) > 0, f"code={code} err={err}")
    if code == 0:
        # Should contain some English
        has_english = any(c.isascii() and c.isalpha() for c in out)
        test("Translation contains English", has_english, f"out={out[:100]}")

    # Test 4: Custom model
    code, out, err = run_transform("transform_claude.py", echo_prompt, "test", model="claude-haiku-4-5-20251001")
    test("Explicit model works", code == 0 and len(out) > 0, f"code={code} err={err}")

    # Test 5: Invalid model → error
    print("\n--- Error handling ---")
    code, out, err = run_transform("transform_claude.py", echo_prompt, "test", model="nonexistent-model-xyz")
    test("Invalid model returns error", code != 0, f"code={code}")
    test("Error message on stderr", "error" in err.lower() or "Error" in err, f"err={err[:100]}")

    # Test 6: Missing prompt file → error
    code, out, err = run_transform("transform_claude.py", "/nonexistent/prompt.md", "test")
    test("Missing prompt file fails", code != 0, f"code={code}")

    # Test 7: No arguments → usage error
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "transform_claude.py")],
        capture_output=True, text=True, timeout=5
    )
    test("No args shows usage", result.returncode != 0, f"code={result.returncode}")

    # Test 8: Long text
    long_text = "This is a test sentence. " * 100  # ~2500 chars
    code, out, err = run_transform("transform_claude.py", echo_prompt, long_text, timeout=60)
    test("Long text (2500 chars)", code == 0 and len(out) > 0, f"code={code} out_len={len(out)}")

    # Test 9: Unicode/emoji
    code, out, err = run_transform("transform_claude.py", echo_prompt, "Hello 🌍 こんにちは мир")
    test("Unicode/emoji input", code == 0 and len(out) > 0, f"code={code}")


# ============================================================
print("\n═══════════════════════════════════════════")
print("TRANSFORM_OPENAI.PY")
print("═══════════════════════════════════════════")
# ============================================================

has_codex = pathlib.Path.home().joinpath(".codex/auth.json").exists()
has_openai_key = bool(os.environ.get("OPENAI_API_KEY", ""))

if not has_codex and not has_openai_key:
    print("  ⚠ Skipping OpenAI tests — no credentials found")
else:
    # Test 1: Basic transform works
    print("\n--- Basic functionality ---")
    code, out, err = run_transform("transform_openai.py", echo_prompt, "Hello world")
    test("OpenAI returns text", code == 0 and len(out) > 0, f"code={code} err={err}")

    # Test 2: Empty input → exit 0
    code, out, err = run_transform("transform_openai.py", echo_prompt, "")
    test("Empty input exits cleanly", code == 0 and out == "", f"code={code} out={out}")

    # Test 3: Translation
    code, out, err = run_transform("transform_openai.py", translate_prompt, "Привет мир")
    test("Russian→English translation", code == 0 and len(out) > 0, f"code={code} err={err}")

    # Test 4: Explicit model (gpt-4o-mini)
    code, out, err = run_transform("transform_openai.py", echo_prompt, "test", model="gpt-4o-mini")
    test("Explicit model gpt-4o-mini", code == 0 and len(out) > 0, f"code={code} err={err}")

    # Test 5: Invalid model → error
    print("\n--- Error handling ---")
    code, out, err = run_transform("transform_openai.py", echo_prompt, "test", model="nonexistent-model-xyz")
    test("Invalid model returns error", code != 0, f"code={code}")

    # Test 6: Missing prompt file
    code, out, err = run_transform("transform_openai.py", "/nonexistent/prompt.md", "test")
    test("Missing prompt file fails", code != 0, f"code={code}")

    # Test 7: No arguments
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "transform_openai.py")],
        capture_output=True, text=True, timeout=5
    )
    test("No args shows usage", result.returncode != 0, f"code={result.returncode}")

    # Test 8: Unicode
    code, out, err = run_transform("transform_openai.py", echo_prompt, "Hello 🌍 мир")
    test("Unicode input", code == 0 and len(out) > 0, f"code={code}")


# ============================================================
print("\n═══════════════════════════════════════════")
print("INTEGRATION: stdin → transform → stdout")
print("═══════════════════════════════════════════")
# ============================================================

if has_claude:
    # Test: pipe chain (simulates SpeechButton flow)
    print("\n--- Claude pipeline ---")
    proc = subprocess.run(
        f'echo "Переведи это на английский" | {sys.executable} {SCRIPTS_DIR}/transform_claude.py {translate_prompt}',
        shell=True, capture_output=True, text=True, timeout=30
    )
    test("Shell pipe works (Claude)", proc.returncode == 0 and len(proc.stdout.strip()) > 0,
         f"code={proc.returncode} err={proc.stderr[:100]}")

if has_codex or has_openai_key:
    print("\n--- OpenAI pipeline ---")
    proc = subprocess.run(
        f'echo "Переведи это на английский" | {sys.executable} {SCRIPTS_DIR}/transform_openai.py {translate_prompt}',
        shell=True, capture_output=True, text=True, timeout=30
    )
    test("Shell pipe works (OpenAI)", proc.returncode == 0 and len(proc.stdout.strip()) > 0,
         f"code={proc.returncode} err={proc.stderr[:100]}")


# ============================================================
# Cleanup
# ============================================================
os.unlink(translate_prompt)
os.unlink(echo_prompt)

print(f"\n═══════════════════════════════════════════")
if failed == 0:
    print(f"ALL {passed} TESTS PASSED ✅")
else:
    print(f"{failed} FAILED, {passed} passed")
print(f"═══════════════════════════════════════════")
sys.exit(1 if failed else 0)
