#!/bin/bash
# Multi-OS Setup and Installation Script for Luna OS

set -e

echo "=== Luna OS Multi-OS Setup & Installation Script ==="

# 1. Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    LIKE=$ID_LIKE
else
    echo "❌ Cannot determine OS. /etc/os-release is missing."
    exit 1
fi

echo "OS Detected: $OS (ID_LIKE: $LIKE)"

# 2. Install System Dependencies based on OS
case "$OS" in
    ubuntu|debian|pop|mint)
        echo "Installing dependencies via apt..."
        sudo apt-get update
        sudo apt-get install -y nodejs npm python3 python3-pip python3-venv mpv policykit-1 adb scrcpy
        ;;
    fedora|rhel|centos)
        echo "Installing dependencies via dnf..."
        sudo dnf install -y nodejs npm python3 python3-pip mpv polkit android-tools scrcpy
        ;;
    arch|manjaro|artix)
        echo "Installing dependencies via pacman..."
        sudo pacman -S --needed --noconfirm nodejs npm python python-pip mpv polkit android-tools scrcpy
        ;;
    *)
        # Try ID_LIKE fallback
        if [[ "$LIKE" == *"arch"* ]]; then
            echo "Falling back to pacman..."
            sudo pacman -S --needed --noconfirm nodejs npm python python-pip mpv polkit android-tools scrcpy
        elif [[ "$LIKE" == *"debian"* ]] || [[ "$LIKE" == *"ubuntu"* ]]; then
            echo "Falling back to apt..."
            sudo apt-get update
            sudo apt-get install -y nodejs npm python3 python3-pip python3-venv mpv policykit-1 adb scrcpy
        elif [[ "$LIKE" == *"fedora"* ]]; then
            echo "Falling back to dnf..."
            sudo dnf install -y nodejs npm python3 python3-pip mpv polkit android-tools scrcpy
        else
            echo "⚠️  Unsupported Linux distribution: $OS."
            echo "Please manually install: nodejs, npm, python3, pip, mpv, polkit, adb, and scrcpy."
            echo "Press ENTER to continue anyway..."
            read -r
        fi
        ;;
esac

# Add user to audio and adb groups if they exist
echo "Adding user to group system links..."
sudo usermod -aG audio $(whoami) 2>/dev/null || true
sudo usermod -aG adb $(whoami) 2>/dev/null || true

# 3. Clean old installations
echo "Cleaning up old installations..."
sudo rm -f /usr/local/bin/luna-os /usr/bin/luna-os /usr/local/bin/Luna-ai /usr/bin/Luna-ai /usr/share/applications/luna-os.desktop
rm -rf ~/.local/opt/luna-os

# 4. Install backend files to /opt/luna-os
echo "Installing Luna OS backend to /opt/luna-os..."
sudo mkdir -p /opt/luna-os
sudo cp -r backend /opt/luna-os/

# Setup python venv in /opt/luna-os
if [ ! -d "/opt/luna-os/venv" ]; then
    echo "Creating Python Virtual Environment..."
    sudo python3 -m venv /opt/luna-os/venv
fi
echo "Installing Python dependencies..."
sudo /opt/luna-os/venv/bin/pip install --upgrade pip
sudo /opt/luna-os/venv/bin/pip install -r requirements.txt

# Copy .env if available
if [ -f ".env" ]; then
    sudo cp .env /opt/luna-os/
fi

# 5. Build and Install desktop application
echo "Installing Node dependencies..."
npm install

echo "Building Tauri desktop application..."
npm run desktop:build || {
    echo "⚠️  Tauri application compilation failed (make sure Rust is installed to build the native client)."
    echo "Note: The web client (npm run dev) is still fully functional."
}

# 6. Copy binary and desktop configurations
if [ -f "src-tauri/target/release/app" ]; then
    echo "Installing Luna OS binary..."
    sudo cp src-tauri/target/release/app /usr/local/bin/luna-os
    sudo chmod +x /usr/local/bin/luna-os
fi

echo "Setting up desktop application shortcut..."
echo "[Desktop Entry]
Name=Luna OS
Comment=Luna OS AI Assistant
Exec=/usr/local/bin/luna-os
Icon=/usr/share/pixmaps/luna-os.png
Terminal=false
Type=Application
Categories=Utility;" | sudo tee /usr/share/applications/luna-os.desktop > /dev/null

if [ -f "src-tauri/icons/128x128.png" ]; then
    sudo cp src-tauri/icons/128x128.png /usr/share/pixmaps/luna-os.png
fi

echo "✅ Installation complete! You can now launch 'Luna OS' or start the web client with 'npm run dev'."
