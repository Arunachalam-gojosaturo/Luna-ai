#!/usr/bin/env bash
# Luna AI - Arch Linux System Application Installer
set -e

echo "====================================================="
echo "  Installing Luna AI Native Application on Arch Linux"
echo "====================================================="

PROJECT_DIR="/home/arunachalam/Luna-ai"
DESKTOP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"

# 1. Create target directories
mkdir -p "$DESKTOP_DIR"
mkdir -p "$BIN_DIR"

# 2. Build production assets if needed
echo "[1/4] Building production assets..."
cd "$PROJECT_DIR"
npm run build

# 3. Create desktop launcher wrapper
echo "[2/4] Installing system binary launcher wrapper 'luna-ai'..."
cat << 'EOF' > "$BIN_DIR/luna-ai"
#!/usr/bin/env bash
PROJECT_DIR="/home/arunachalam/Luna-ai"
cd "$PROJECT_DIR"
exec "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/luna_desktop.py" "$@"
EOF
chmod +x "$BIN_DIR/luna-ai"

# Also create shortcut 'luna'
cat << 'EOF' > "$BIN_DIR/luna"
#!/usr/bin/env bash
exec "$HOME/.local/bin/luna-ai" "$@"
EOF
chmod +x "$BIN_DIR/luna"

# 4. Install Desktop Entry
echo "[3/4] Installing Desktop Entry to $DESKTOP_DIR/Luna-AI.desktop..."
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

# 5. Update desktop database
echo "[4/4] Refreshing application menu database..."
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
