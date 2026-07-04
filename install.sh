#!/bin/bash
# Install Luna OS v2 to Arch Linux

set -e

INSTALL_DIR="/opt/luna-os"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"

echo "🌙 Luna OS v2 - Arch Linux Installation"
echo "========================================"

# Check if running as root for system installation
if [[ $EUID -eq 0 ]]; then
    INSTALL_DIR="/opt/luna-os"
    BIN_DIR="/usr/bin"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor"
    echo "Installing system-wide to $INSTALL_DIR"
else
    INSTALL_DIR="$HOME/.local/opt/luna-os"
    BIN_DIR="$HOME/.local/bin"
    echo "Installing user-local to $INSTALL_DIR"
fi

# Install system dependencies
echo "📦 Checking system dependencies..."
MISSING_DEPS=()

command -v python3 >/dev/null 2>&1 || MISSING_DEPS+=("python")
command -v node >/dev/null 2>&1 || MISSING_DEPS+=("nodejs")
command -v rustc >/dev/null 2>&1 || MISSING_DEPS+=("rust")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠️  Missing dependencies: ${MISSING_DEPS[*]}"
    if [[ $EUID -eq 0 ]]; then
        echo "Installing with pacman..."
        pacman -Sy --needed "${MISSING_DEPS[@]}"
    else
        echo "Please install: sudo pacman -S ${MISSING_DEPS[*]}"
        exit 1
    fi
fi

# Install audio & portal libraries for voice features
echo "📦 Checking audio & portal libraries..."
AUDIO_LIBS=("portaudio" "libffi" "base-devel" "pipewire" "pipewire-pulse" "wireplumber" "xdg-desktop-portal" "xdg-desktop-portal-wlr")

MISSING_AUDIO=()
for lib in "${AUDIO_LIBS[@]}"; do
    pacman -Q "$lib" >/dev/null 2>&1 || MISSING_AUDIO+=("$lib")
done

if [ ${#MISSING_AUDIO[@]} -gt 0 ]; then
    echo "⚠️  Missing audio/portal packages: ${MISSING_AUDIO[*]}"
    if [[ $EUID -eq 0 ]]; then
        echo "Installing with pacman..."
        pacman -Sy --needed "${MISSING_AUDIO[@]}"
    else
        echo "Install with: sudo pacman -S ${MISSING_AUDIO[*]}"
    fi
fi

# Ensure user is in audio group (necessary for microphone access)
if [[ $EUID -ne 0 ]]; then
    if ! id -nG "$USER" | grep -qw audio; then
        echo "⚠️  Current user is not in 'audio' group. Adding via sudo..."
        echo "Run: sudo usermod -aG audio $USER"
    fi
else
    echo "Note: running as root — ensure non-root user is in 'audio' group for desktop sessions."
fi

# Restart user services to apply portal/pipewire
echo "🔁 Restarting user services (pipewire & xdg-desktop-portal)..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user restart pipewire || true
    systemctl --user restart wireplumber || true
    systemctl --user restart xdg-desktop-portal || true
    systemctl --user restart xdg-desktop-portal-wlr || true
fi

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy application files
echo "📋 Copying application files..."
cp -r . "$INSTALL_DIR/"

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Build frontend
echo "🎨 Building React frontend..."
npm install
npm run build

# Build desktop app
echo "🖥️  Building Tauri desktop app..."
npm run desktop:build

# Create wrapper script
echo "🔗 Creating launcher script..."
cat > "$BIN_DIR/luna-os" << 'EOF'
#!/bin/bash
# Luna OS launcher
export LUNA_OS_HOME="INSTALL_DIR_PLACEHOLDER"
cd "$LUNA_OS_HOME"
exec "$LUNA_OS_HOME/src-tauri/target/release/app" "$@"
EOF

sed -i "s|INSTALL_DIR_PLACEHOLDER|$INSTALL_DIR|g" "$BIN_DIR/luna-os"
chmod +x "$BIN_DIR/luna-os"

# Create desktop file
echo "🖱️  Installing desktop file..."
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/luna-os.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Luna OS v2
Comment=AI-powered Operating System for Arch Linux
Exec=$BIN_DIR/luna-os
Icon=$INSTALL_DIR/src-tauri/icons/128x128.png
Categories=Utility;Development;
Terminal=false
StartupNotify=true
EOF

chmod 644 "$DESKTOP_DIR/luna-os.desktop"

# Install icons
echo "🎨 Installing application icons..."
mkdir -p "$ICON_DIR/128x128/apps"
cp "src-tauri/icons/128x128.png" "$ICON_DIR/128x128/apps/luna-os.png"

echo ""
echo "✅ Luna OS v2 installation complete!"
echo ""
echo "📍 Installation location: $INSTALL_DIR"
echo "🚀 Launch command: luna-os"
echo "🖱️  Desktop shortcut: Luna OS v2"
echo ""
echo "First run will take a moment to start the Python backend..."
