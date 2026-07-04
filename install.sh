#!/bin/bash

echo "Cleaning up old installations..."
sudo rm -f /usr/local/bin/luna-os /usr/bin/luna-os /usr/local/bin/Luna-ai /usr/bin/Luna-ai /usr/share/applications/luna-os.desktop
rm -rf ~/.local/opt/luna-os

echo "Installing Luna OS backend to /opt/luna-os..."
sudo mkdir -p /opt/luna-os
sudo cp -r backend /opt/luna-os/
# Ensure venv exists or create it
if [ ! -d "/opt/luna-os/venv" ]; then
  if [ -d "venv" ]; then
    sudo cp -r venv /opt/luna-os/
  else
    sudo python3 -m venv /opt/luna-os/venv
    sudo /opt/luna-os/venv/bin/pip install -r requirements.txt
  fi
fi
# Copy .env if available
if [ -f ".env" ]; then
  sudo cp .env /opt/luna-os/
fi

echo "Installing Luna OS binary..."
sudo cp src-tauri/target/release/app /usr/local/bin/luna-os
sudo chmod +x /usr/local/bin/luna-os

echo "Setting up desktop application shortcut..."
echo "[Desktop Entry]
Name=Luna OS
Comment=Luna OS AI Assistant
Exec=/usr/local/bin/luna-os
Icon=/usr/share/pixmaps/luna-os.png
Terminal=false
Type=Application
Categories=Utility;" | sudo tee /usr/share/applications/luna-os.desktop > /dev/null

sudo cp src-tauri/icons/128x128.png /usr/share/pixmaps/luna-os.png

echo "✅ Installation complete! You can now launch 'Luna OS' from your application menu or terminal."
