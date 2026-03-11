#!/usr/bin/env bash
# ─────────────────────────────────────────────────
#   L.U.N.A. AI  v5.0  —  Launch script
# ─────────────────────────────────────────────────
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   L · U · N · A   AI   v5.0  Setup     ║"
echo "  ╚══════════════════════════════════════════╝"

PYTHON="${PYTHON:-python3}"
VENV="$DIR/.venv"

if ! command -v "$PYTHON" &>/dev/null; then
    echo "  [✗] python3 not found"; exit 1
fi
echo "  [✓] Python: $($PYTHON --version)"

[ ! -d "$VENV" ] && echo "  [~] Creating venv..." && "$PYTHON" -m venv "$VENV"

# Activate (bash / fish)
if [ -n "$FISH_VERSION" ]; then
    source "$VENV/bin/activate.fish"
else
    source "$VENV/bin/activate"
fi
echo "  [✓] Venv activated"

echo "  [~] Installing dependencies..."
pip install -q --upgrade pip 2>/dev/null || true
pip install -q -r requirements.txt 2>/dev/null || \
    pip install -q -r requirements.txt --break-system-packages

# Optional: pyaudio (mic input)
pip install -q pyaudio 2>/dev/null || echo "  [~] pyaudio skipped (mic input optional)"

echo "  [✓] Ready"
echo ""
echo "  ✨  Launching Luna AI v5..."
echo "  💡  Tip: Click ⚙ Settings → add Gemini or Groq API key"
echo ""

python main.py
