#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  LUNA AI v6 — Universal Installer                                  ║
# ║  • Auto-detects OS, package manager, shell                         ║
# ║  • Installs to /opt/luna-ai (system-wide)                          ║
# ║  • Builds venv with correct Python (pyenv-safe)                    ║
# ║  • TMPDIR=/tmp fix for Python 3.14                                  ║
# ║  • Creates: /usr/local/bin/luna | fish fn | .desktop               ║
# ║                                                                    ║
# ║  IMPORTANT: Run from OUTSIDE /opt/luna-ai                          ║
# ║    cd ~ && bash /path/to/this/install.sh                           ║
# ╚══════════════════════════════════════════════════════════════════════╝
set -euo pipefail

GRN='\033[0;32m'; YLW='\033[1;33m'; RED='\033[0;31m'; CYN='\033[0;36m'; BLD='\033[1m'; NC='\033[0m'
ok()  { echo -e "  ${GRN}[✓]${NC} $1"; }
inf() { echo -e "  ${YLW}[→]${NC} $1"; }
err() { echo -e "  ${RED}[✗]${NC} $1"; exit 1; }
hdr() { echo -e "\n  ${CYN}${BLD}━━━ $1 ━━━${NC}"; }

echo ""
echo -e "  ${CYN}${BLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${CYN}${BLD}║   L.U.N.A. AI v6 — Universal Installer        ║${NC}"
echo -e "  ${CYN}${BLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="/opt/luna-ai"
VENV="$DEST/venv"
VPYTHON="$VENV/bin/python3"
VPIP="$VENV/bin/pip"

[ -f "$SRC/main.py" ] || err "main.py not found. Run this script from the Luna-ai folder."
ok "Source: $SRC"

# Guard: don't run from inside destination
if [[ "$SRC" == "$DEST"* ]]; then
    err "Do not run this script from inside $DEST.\nCopy install.sh somewhere else first:\n  cp $SRC/install.sh ~/\n  cd ~ && bash install.sh"
fi

# ═══════════════════════════════════════════════════
#  1. OS DETECTION
# ═══════════════════════════════════════════════════
hdr "DETECTING SYSTEM"
IS_ARCH=false; IS_DEBIAN=false; IS_FEDORA=false; IS_MACOS=false
PKG_MGR="unknown"; OS_ID="unknown"

if [[ "$OSTYPE" == "darwin"* ]]; then
    IS_MACOS=true; OS_ID="macos"
    command -v brew &>/dev/null && PKG_MGR="brew" || err "Install Homebrew first: https://brew.sh"
elif [ -f /etc/os-release ]; then
    source /etc/os-release
    OS_ID="${ID:-unknown}"
    case "${ID:-}${ID_LIKE:-}" in
        *arch*)
            IS_ARCH=true
            command -v yay  &>/dev/null && PKG_MGR="yay"  || \
            command -v paru &>/dev/null && PKG_MGR="paru" || PKG_MGR="pacman" ;;
        *debian*|*ubuntu*) IS_DEBIAN=true; PKG_MGR="apt"  ;;
        *fedora*|*rhel*)   IS_FEDORA=true
            command -v dnf &>/dev/null && PKG_MGR="dnf" || PKG_MGR="yum" ;;
        *) PKG_MGR="unknown" ;;
    esac
fi
ok "OS: $OS_ID  |  pkg: $PKG_MGR"

# ═══════════════════════════════════════════════════
#  2. FIND REAL PYTHON (skip pyenv shims + active venv)
# ═══════════════════════════════════════════════════
hdr "DETECTING PYTHON"
REAL_PY=""

# Try pyenv actual version directories (not shims)
if command -v pyenv &>/dev/null; then
    PYENV_ROOT="$(pyenv root 2>/dev/null || echo "$HOME/.pyenv")"
    while IFS= read -r vd; do
        for c in "$vd/bin/python3" "$vd/bin/python"; do
            [ -x "$c" ] && { REAL_PY="$c"; break 2; }
        done
    done < <(find "$PYENV_ROOT/versions" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort -rV)
fi

# System python (guaranteed real binary)
if [ -z "$REAL_PY" ]; then
    for c in /usr/bin/python3 /usr/local/bin/python3 /usr/bin/python; do
        [ -x "$c" ] && { REAL_PY="$c"; break; }
    done
fi
[ -z "$REAL_PY" ] && err "No Python 3 found. Install: sudo pacman -S python"
ok "Python: $REAL_PY  ($($REAL_PY --version 2>&1))"

# ═══════════════════════════════════════════════════
#  3. SYSTEM PACKAGES
# ═══════════════════════════════════════════════════
hdr "SYSTEM PACKAGES"

if $IS_ARCH; then
    inf "Installing python-pyqt6, mpv, portaudio..."
    sudo pacman -S --noconfirm --needed python python-pyqt6 mpv portaudio 2>/dev/null || true
elif $IS_DEBIAN; then
    sudo apt-get install -y python3-pyqt6 mpv portaudio19-dev 2>/dev/null || true
elif $IS_FEDORA; then
    sudo $PKG_MGR install -y python3-PyQt6 mpv portaudio-devel 2>/dev/null || true
elif $IS_MACOS; then
    brew install mpv portaudio 2>/dev/null || true
fi

command -v mpv &>/dev/null && ok "mpv ✓" || inf "mpv not found — will use pygame fallback"
ok "System packages done"

# ═══════════════════════════════════════════════════
#  4. COPY TO /opt/luna-ai  (cp, no rsync)
# ═══════════════════════════════════════════════════
hdr "INSTALLING TO $DEST"

inf "Removing old installation..."
sudo rm -rf "$DEST"
sudo mkdir -p "$DEST"

inf "Copying files..."
# Use tar to exclude unwanted dirs/files, pipe to destination
(
    cd "$SRC"
    tar --exclude="./.git" \
        --exclude="./venv" \
        --exclude="./.venv" \
        --exclude="./__pycache__" \
        --exclude="**/__pycache__" \
        --exclude="*.pyc" \
        --exclude="*.zip" \
        -cf - . | sudo tar -xf - -C "$DEST"
)

sudo chown -R "$USER:$USER" "$DEST"
ok "Files installed to $DEST"

# ═══════════════════════════════════════════════════
#  5. FRESH VENV
# ═══════════════════════════════════════════════════
hdr "BUILDING VENV"

inf "Removing old venv..."
rm -rf "$VENV"

inf "Creating venv with $REAL_PY..."
"$REAL_PY" -m venv "$VENV"
ok "venv: $("$VPYTHON" --version 2>&1)"

inf "Upgrading pip (TMPDIR=/tmp)..."
TMPDIR=/tmp "$VPIP" install -q --upgrade pip 2>/dev/null || true

inf "Installing packages..."
TMPDIR=/tmp "$VPIP" install -q \
    PyQt6 \
    edge-tts \
    google-genai \
    groq \
    requests \
    psutil \
    yt-dlp \
    SpeechRecognition \
    beautifulsoup4 \
    pygame

inf "PyAudio (optional mic)..."
TMPDIR=/tmp "$VPIP" install -q pyaudio 2>/dev/null \
    && ok "PyAudio installed" \
    || inf "PyAudio skipped (mic won't work, everything else fine)"

ok "Python packages installed"

# ═══════════════════════════════════════════════════
#  6. GLOBAL LAUNCHER
# ═══════════════════════════════════════════════════
hdr "CREATING COMMAND"

sudo tee /usr/local/bin/luna > /dev/null << LAUNCH
#!/usr/bin/env bash
export DISPLAY="\${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-wayland-1}"
export DBUS_SESSION_BUS_ADDRESS="\${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/\$(id -u)/bus}"
export QT_QPA_PLATFORM="\${QT_QPA_PLATFORM:-wayland}"
export MOZ_ENABLE_WAYLAND=1
export TMPDIR=/tmp
exec $VPYTHON $DEST/main.py "\$@"
LAUNCH
sudo chmod +x /usr/local/bin/luna
ok "Command: /usr/local/bin/luna"

# Fish function
FISH_DIR="$HOME/.config/fish/functions"
mkdir -p "$FISH_DIR"
printf 'function luna\n    /usr/local/bin/luna $argv\nend\n' > "$FISH_DIR/luna.fish"
ok "Fish function: luna"

# Bash/Zsh alias
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    [ -f "$RC" ] || continue
    grep -q "alias luna=" "$RC" && \
        sed -i "s|alias luna=.*|alias luna='/usr/local/bin/luna'|" "$RC" || \
        echo "alias luna='/usr/local/bin/luna'" >> "$RC"
done

# .desktop
mkdir -p "$HOME/.local/share/applications"
ICON=$(find "$DEST/assets" -name "*.png" 2>/dev/null | head -1 || echo "dialog-information")
cat > "$HOME/.local/share/applications/luna-ai.desktop" << DESKTOP
[Desktop Entry]
Name=Luna AI
Comment=Hacker-style AI assistant with voice control
Exec=/usr/local/bin/luna
Icon=$ICON
Terminal=false
Type=Application
Categories=Utility;AI;
Keywords=AI;voice;assistant;luna;
DESKTOP
ok ".desktop entry created"

# ═══════════════════════════════════════════════════
#  7. TTS SMOKE TEST
# ═══════════════════════════════════════════════════
hdr "TESTING VOICE"

TMP=$(mktemp /tmp/luna_tts_XXXXX.mp3)
inf "Synthesizing test audio..."
if TMPDIR=/tmp "$VPYTHON" -m edge_tts \
    --voice "en-US-AriaNeural" \
    --text "Luna online. Voice ready, Boss." \
    --write-media "$TMP" 2>/dev/null && [ -s "$TMP" ]; then
    ok "edge_tts ✓  ($(du -h "$TMP" | cut -f1))"
    if command -v mpv &>/dev/null; then
        mpv --no-video --really-quiet "$TMP" 2>/dev/null && ok "Audio playback ✓" || true
    fi
    rm -f "$TMP"
else
    rm -f "$TMP"
    echo -e "  ${RED}[!]${NC} TTS failed — check internet or run: $VPYTHON -m edge_tts --list-voices"
fi

# ═══════════════════════════════════════════════════
#  8. DONE
# ═══════════════════════════════════════════════════
echo ""
echo -e "  ${GRN}${BLD}╔════════════════════════════════════════════════════╗${NC}"
echo -e "  ${GRN}${BLD}║   L.U.N.A. AI v6 INSTALLED  ✓                   ║${NC}"
echo -e "  ${GRN}${BLD}╠════════════════════════════════════════════════════╣${NC}"
echo -e "  ${GRN}${BLD}║  App    → /opt/luna-ai                           ║${NC}"
echo -e "  ${GRN}${BLD}║  Venv   → /opt/luna-ai/venv                      ║${NC}"
echo -e "  ${GRN}${BLD}║  Run    → luna  (from any shell, anywhere)       ║${NC}"
echo -e "  ${GRN}${BLD}║                                                  ║${NC}"
echo -e "  ${GRN}${BLD}║  First run: Open ⚙ Settings → add API key        ║${NC}"
echo -e "  ${GRN}${BLD}║  Gemini: aistudio.google.com (free)              ║${NC}"
echo -e "  ${GRN}${BLD}║  Groq:   console.groq.com   (free, fast)         ║${NC}"
echo -e "  ${GRN}${BLD}╚════════════════════════════════════════════════════╝${NC}"
echo ""
