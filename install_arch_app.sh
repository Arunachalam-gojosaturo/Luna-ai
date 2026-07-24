#!/usr/bin/env bash
# Luna AI - Arch Linux System Application Installer
set -e

echo "====================================================="
echo "  Installing Luna AI Native Application on Arch Linux"
echo "====================================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"

# 1. Create target directories
mkdir -p "$DESKTOP_DIR"
mkdir -p "$BIN_DIR"

# 2. Build production assets if needed
echo "[1/5] Building production assets..."
cd "$PROJECT_DIR"
npm run build

# 3. Create Python venv if not existing
echo "[2/5] Setting up Python virtual environment..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi
"$PROJECT_DIR/venv/bin/pip" install --upgrade pip -q
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q || true
fi

# 4. Create desktop launcher wrappers
echo "[3/5] Installing system binary launcher wrapper 'luna-ai'..."
cat << EOF > "$BIN_DIR/luna-ai"
#!/usr/bin/env bash
PROJECT_DIR="$PROJECT_DIR"
cd "\$PROJECT_DIR"
if [ -f "\$PROJECT_DIR/venv/bin/python" ]; then
    exec "\$PROJECT_DIR/venv/bin/python" "\$PROJECT_DIR/luna_desktop.py" "\$@"
else
    exec python3 "\$PROJECT_DIR/luna_desktop.py" "\$@"
fi
EOF
chmod +x "$BIN_DIR/luna-ai"

# Also create shortcut 'luna'
cat << EOF > "$BIN_DIR/luna"
#!/usr/bin/env bash
exec "$BIN_DIR/luna-ai" "\$@"
EOF
chmod +x "$BIN_DIR/luna"

# CLI Launcher 'luna-cli'
cat << EOF > "$BIN_DIR/luna-cli"
#!/usr/bin/env bash
PROJECT_DIR="$PROJECT_DIR"
cd "\$PROJECT_DIR"
if [ -f "\$PROJECT_DIR/venv/bin/python" ]; then
    exec "\$PROJECT_DIR/venv/bin/python" "\$PROJECT_DIR/luna_cli_enhanced.py" "\$@"
else
    exec python3 "\$PROJECT_DIR/luna_cli_enhanced.py" "\$@"
fi
EOF
chmod +x "$BIN_DIR/luna-cli"

# 5. Install Desktop Entry
echo "[4/5] Installing Desktop Entry to $DESKTOP_DIR/Luna-AI.desktop..."
cat << EOF > "$DESKTOP_DIR/Luna-AI.desktop"
[Desktop Entry]
Name=Luna AI
Comment=Autonomous Personal AI Operating System & Daily Companion
Exec=$BIN_DIR/luna-ai
Icon=$PROJECT_DIR/public/deskopticon.png
Terminal=false
Type=Application
Categories=Utility;Development;System;
Keywords=AI;Assistant;OperatingSystem;Hyprland;Luna;
EOF
chmod +x "$DESKTOP_DIR/Luna-AI.desktop"

# 6. Update desktop database
echo "[5/5] Refreshing application menu database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" &> /dev/null || true
fi

echo "====================================================="
echo "  SUCCESS! Luna AI Application Installed Successfully!"
echo ""
echo "  You can now launch Luna AI anywhere on Arch Linux by:"
echo "  1. Typing 'luna-ai' or 'luna' in your terminal."
echo "  2. Selecting 'Luna AI' from Rofi / Wofi / Hyprland application menu."
echo "====================================================="
