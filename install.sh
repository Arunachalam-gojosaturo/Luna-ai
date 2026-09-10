#!/usr/bin/env bash
# ==============================================================================
#  Luna AI (Luna OS X) — Universal Multi-Linux Installer
#  Supports: Arch Linux, Ubuntu, Debian, Pop!_OS, Linux Mint, Fedora, RHEL, openSUSE, Alpine
#
#  One-Line Installation Command:
#  curl -sSL https://raw.githubusercontent.com/Arunachalam-gojosaturo/Luna-ai/main/install.sh | bash
# ==============================================================================

set -e

REPO_URL="https://github.com/Arunachalam-gojosaturo/Luna-ai.git"
INSTALL_DIR="$HOME/.local/share/luna-ai"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "======================================================================"
echo " 🌙 Luna AI (Luna OS X) — Universal Linux Installer"
echo "======================================================================"

# 1. Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    LIKE=$ID_LIKE
else
    DISTRO="unknown"
    LIKE="unknown"
fi

echo "▸ OS Detected: ${NAME:-$DISTRO} ($DISTRO)"

# Function to check command availability
has_cmd() {
    command -v "$1" &>/dev/null
}

# Use sudo if available and not root
SUDO=""
if [ "$EUID" -ne 0 ] && has_cmd sudo; then
    SUDO="sudo"
fi

echo "▸ Installing system dependencies..."
case "$DISTRO" in
    arch|manjaro|artix|endeavouros|garuda)
        $SUDO pacman -S --needed --noconfirm nodejs npm python python-pip mpv polkit qt6-webengine python-pyqt6 git curl wl-clipboard jq libnotify espeak-ng soundfile libpulse alsa-utils || true
        ;;
    ubuntu|debian|pop|mint|elementary)
        $SUDO apt-get update -qq || true
        $SUDO apt-get install -y nodejs npm python3 python3-pip python3-venv mpv policykit-1 git curl python3-pyqt6 wl-clipboard jq libnotify-bin espeak-ng libsndfile1 portaudio19-dev || true
        ;;
    fedora|rhel|centos|rocky|almalinux)
        $SUDO dnf install -y nodejs npm python3 python3-pip mpv polkit git curl python3-pyqt6 python3-pyqt6-webengine wl-clipboard jq libnotify espeak-ng libsndfile portaudio-devel || true
        ;;
    opensuse*|suse)
        $SUDO zypper install -y nodejs npm python3 python3-pip mpv polkit git curl python3-qt6 wl-clipboard jq libnotify-tools espeak-ng libsndfile portaudio-devel || true
        ;;
    alpine)
        $SUDO apk add nodejs npm python3 py3-pip mpv polkit git curl jq || true
        ;;
    *)
        if [[ "$LIKE" == *"arch"* ]]; then
            $SUDO pacman -S --needed --noconfirm nodejs npm python python-pip mpv polkit qt6-webengine python-pyqt6 git curl wl-clipboard jq libnotify espeak-ng soundfile libpulse alsa-utils || true
        elif [[ "$LIKE" == *"debian"* ]] || [[ "$LIKE" == *"ubuntu"* ]]; then
            $SUDO apt-get update -qq || true
            $SUDO apt-get install -y nodejs npm python3 python3-pip python3-venv mpv policykit-1 git curl python3-pyqt6 wl-clipboard jq libnotify-bin espeak-ng libsndfile1 || true
        elif [[ "$LIKE" == *"fedora"* ]]; then
            $SUDO dnf install -y nodejs npm python3 python3-pip mpv polkit git curl python3-pyqt6 python3-pyqt6-webengine wl-clipboard jq libnotify espeak-ng libsndfile || true
        else
            echo "⚠️ Custom Linux distribution detected. Proceeding with environment packages..."
        fi
        ;;
esac

# Add user to audio and adb groups if available
$SUDO usermod -aG audio "$(whoami)" 2>/dev/null || true
$SUDO usermod -aG adb "$(whoami)" 2>/dev/null || true

# 2. Check source location (Remote execution via curl vs Local execution)
CURRENT_DIR="$(pwd)"
if [ -f "$CURRENT_DIR/luna_desktop.py" ] && [ -f "$CURRENT_DIR/package.json" ]; then
    echo "▸ Using local repository directory: $CURRENT_DIR"
    TARGET_DIR="$CURRENT_DIR"
else
    echo "▸ Downloading/updating Luna AI source to $INSTALL_DIR..."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    if [ -d "$INSTALL_DIR/.git" ]; then
        cd "$INSTALL_DIR"
        git pull origin main
    else
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    TARGET_DIR="$INSTALL_DIR"
fi

cd "$TARGET_DIR"

# 3. Create Python Virtual Environment & Install Dependencies
echo "▸ Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/python -m pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    echo "▸ Installing Python dependencies from requirements.txt..."
    ./venv/bin/pip install -r requirements.txt -q
fi

# Ensure PyQt6 & Kokoro ONNX are properly loaded
./venv/bin/python -c "import PyQt6" 2>/dev/null || ./venv/bin/pip install PyQt6 PyQt6-WebEngine -q || true
./venv/bin/python -c "import kokoro_onnx, soundfile" 2>/dev/null || ./venv/bin/pip install kokoro-onnx soundfile sounddevice -q || true

# 4. Provision Kokoro-ONNX Offline Neural TTS Models
MODEL_DIR="$HOME/.local/share/luna-ai/models"
mkdir -p "$MODEL_DIR"
mkdir -p "$TARGET_DIR/models"

echo "▸ Checking Kokoro-ONNX offline TTS models..."
# Check kokoro-v1.0.onnx
if [ ! -f "$MODEL_DIR/kokoro-v1.0.onnx" ] && [ ! -f "$TARGET_DIR/models/kokoro-v1.0.onnx" ]; then
    if [ -f "/home/arunachalam/testtts/kokoro-v1.0.onnx" ]; then
        echo "▸ Linking existing local Kokoro model from /home/arunachalam/testtts..."
        cp "/home/arunachalam/testtts/kokoro-v1.0.onnx" "$MODEL_DIR/kokoro-v1.0.onnx"
    else
        echo "▸ Downloading Kokoro-ONNX v1.0 offline model (325MB)..."
        curl -L --progress-bar "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx" -o "$MODEL_DIR/kokoro-v1.0.onnx" || echo "⚠️ Kokoro model download skipped. Fallback TTS will be used."
    fi
fi

# Check voices-v1.0.bin
if [ ! -f "$MODEL_DIR/voices-v1.0.bin" ] && [ ! -f "$TARGET_DIR/models/voices-v1.0.bin" ]; then
    if [ -f "/home/arunachalam/testtts/voices-v1.0.bin" ]; then
        echo "▸ Linking existing local Kokoro voices from /home/arunachalam/testtts..."
        cp "/home/arunachalam/testtts/voices-v1.0.bin" "$MODEL_DIR/voices-v1.0.bin"
    else
        echo "▸ Downloading Kokoro voice bank (voices-v1.0.bin)..."
        curl -L --progress-bar "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" -o "$MODEL_DIR/voices-v1.0.bin" || echo "⚠️ Kokoro voices download skipped."
    fi
fi

# 5. Install Node Dependencies & Build Frontend Assets
echo "▸ Installing Node.js dependencies..."
npm install --silent

echo "▸ Building production web assets..."
npm run build

# Make auxiliary scripts executable
chmod +x "$TARGET_DIR/scripts/luna_hypr_ai.sh" 2>/dev/null || true

# 6. Install Binary Launchers & Desktop Application Entry
echo "▸ Installing system launcher scripts and menu desktop entry..."
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Primary Launcher Script 'luna-ai'
cat << EOF > "$BIN_DIR/luna-ai"
#!/usr/bin/env bash
cd "$TARGET_DIR"
exec "$TARGET_DIR/venv/bin/python" "$TARGET_DIR/luna_desktop.py" "\$@"
EOF
chmod +x "$BIN_DIR/luna-ai"

# Short Launcher Alias 'luna'
cat << EOF > "$BIN_DIR/luna"
#!/usr/bin/env bash
exec "$BIN_DIR/luna-ai" "\$@"
EOF
chmod +x "$BIN_DIR/luna"

# CLI Launcher 'luna-cli'
cat << EOF > "$BIN_DIR/luna-cli"
#!/usr/bin/env bash
cd "$TARGET_DIR"
exec "$TARGET_DIR/venv/bin/python" "$TARGET_DIR/luna_cli_enhanced.py" "\$@"
EOF
chmod +x "$BIN_DIR/luna-cli"

# Hyprland Quick-Action Launcher 'luna-hypr'
cat << EOF > "$BIN_DIR/luna-hypr"
#!/usr/bin/env bash
exec "$TARGET_DIR/scripts/luna_hypr_ai.sh" "\$@"
EOF
chmod +x "$BIN_DIR/luna-hypr"

# Desktop Application Entry (.desktop)
cat << EOF > "$DESKTOP_DIR/Luna-AI.desktop"
[Desktop Entry]
Name=Luna AI
Comment=Autonomous Personal AI Operating System & Daily Companion
Exec=$BIN_DIR/luna-ai
Icon=$TARGET_DIR/public/deskopticon.png
Terminal=false
Type=Application
Categories=Utility;Development;System;
Keywords=AI;Assistant;OperatingSystem;Hyprland;Luna;
EOF
chmod +x "$DESKTOP_DIR/Luna-AI.desktop"

# Refresh desktop database
if has_cmd update-desktop-database; then
    update-desktop-database "$DESKTOP_DIR" &>/dev/null || true
fi

# Check PATH
PATH_NOTICE=""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    PATH_NOTICE="⚠️  Notice: Make sure '$BIN_DIR' is in your PATH. Add 'export PATH=\"\$HOME/.local/bin:\$PATH\"' to your ~/.bashrc or ~/.zshrc."
fi

echo "======================================================================"
echo " ✨ SUCCESS! Luna AI has been installed successfully on your system!"
echo "======================================================================"
echo ""
echo " 🚀 How to Launch Luna AI:"
echo "   1. GUI App:        Type 'luna-ai' or 'luna' in your terminal"
echo "   2. App Launcher:   Select 'Luna AI' from Rofi, Wofi, or Hyprland menu"
echo "   3. CLI Mode:       Type 'luna-cli' in your terminal"
echo "   4. Hyprland AI:    Run 'luna-hypr --prompt' or 'luna-hypr --selection'"
echo ""
if [ -n "$PATH_NOTICE" ]; then
    echo "$PATH_NOTICE"
    echo ""
fi
echo " 💡 Hyprland Recommended Keybindings (~/.config/hypr/hyprland.conf):"
echo "   bind = \$mainMod, SPACE, exec, luna-hypr --selection"
echo "   bind = \$mainMod SHIFT, SPACE, exec, luna-hypr --prompt"
echo "   bind = \$mainMod, V, exec, luna-hypr --voice"
echo ""
echo " 🌐 Universal One-Line Install Command:"
echo "   curl -sSL https://raw.githubusercontent.com/Arunachalam-gojosaturo/Luna-ai/main/install.sh | bash"
echo "======================================================================"
