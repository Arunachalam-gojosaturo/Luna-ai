#!/usr/bin/env bash

set -e

APP_NAME="luna-ai"
SRC_DIR="/home/saturogojo/Music/Luna-AI-v5"
INSTALL_DIR="/usr/share/luna-ai"
BIN_PATH="/usr/bin/luna-ai"
DESKTOP_FILE="/usr/share/applications/luna-ai.desktop"
ICON_PATH="/usr/share/pixmaps/luna-ai.png"

echo "Installing LUNA AI..."

if [ ! -d "$SRC_DIR" ]; then
    echo "Source directory not found!"
    exit 1
fi

echo "Creating install directory..."
sudo mkdir -p "$INSTALL_DIR"

echo "Copying project..."
sudo cp -r "$SRC_DIR"/* "$INSTALL_DIR"

echo "Creating launcher..."

sudo tee "$BIN_PATH" > /dev/null <<'EOF'
#!/usr/bin/env bash

cd /usr/share/luna-ai

if [ -f venv/bin/activate.fish ]; then
    exec fish -c "source venv/bin/activate.fish; python main.py"
else
    python main.py
fi
EOF

sudo chmod +x "$BIN_PATH"

echo "Creating desktop entry..."

sudo tee "$DESKTOP_FILE" > /dev/null <<EOF
[Desktop Entry]
Name=LUNA AI
Comment=Language Understanding Neural Agent
Exec=luna-ai
Icon=luna-ai
Terminal=false
Type=Application
Categories=Utility;Development;AI;
EOF

echo "Installing icon..."

if [ -f "$SRC_DIR/icon.png" ]; then
    sudo cp "$SRC_DIR/icon.png" "$ICON_PATH"
fi

echo "Refreshing desktop database..."
sudo update-desktop-database /usr/share/applications 2>/dev/null || true

echo ""
echo "LUNA AI installed!"
echo "Run using:"
echo "   luna-ai"
echo "or open from launcher."
