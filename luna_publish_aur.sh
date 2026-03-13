#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   LUNA AI — GITHUB + AUR PUBLISH (ALL-IN-ONE)              ║
# ║   Run from: ~/Downloads/Luna-ai                            ║
# ║   Usage: ./luna_publish_aur.sh Arunachalam-gojosatoru      ║
# ╚══════════════════════════════════════════════════════════════╝
GITHUB_USER="${1:-Arunachalam-gojosaturo}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$HOME/aur-luna-ai"

GRN='\033[0;32m'; YLW='\033[1;33m'; CYN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
ok()  { echo -e "  ${GRN}[✓]${NC} $1"; }
inf() { echo -e "  ${YLW}[→]${NC} $1"; }
hdr() { echo -e "\n  ${CYN}━━━ $1 ━━━${NC}"; }
err() { echo -e "  ${RED}[!]${NC} $1"; }

echo ""
echo -e "  ${CYN}╔══════════════════════════════════════════════╗${NC}"
echo -e "  ${CYN}║   LUNA AI — GITHUB + AUR PUBLISHER         ║${NC}"
echo -e "  ${CYN}║   GitHub: $GITHUB_USER                     ║${NC}"
echo -e "  ${CYN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ══════════════════════════════════════════════
# STEP 1: Fix dependencies in PKGBUILD
# ══════════════════════════════════════════════
hdr "FIXING PKGBUILD DEPENDENCIES"

# Install the actual missing packages on this machine
inf "Installing python-pyqt6 and yt-dlp..."
sudo pacman -S --noconfirm --needed python-pyqt6 yt-dlp 2>/dev/null || true
ok "Dependencies installed"

# Fix the PKGBUILD — use correct Arch package names
cat > "$PKG_DIR/PKGBUILD" << PKGEOF
# Maintainer: Arunachalam <$GITHUB_USER@users.noreply.github.com>
pkgname=luna-ai
pkgver=1.0.0
pkgrel=1
pkgdesc="Luna AI - Hacker-style voice AI assistant for Arch Linux + Hyprland with YouTube, brightness and volume control"
arch=('any')
url="https://github.com/$GITHUB_USER/luna-ai"
license=('MIT')
depends=(
    'python>=3.10'
    'python-pyqt6'
    'firefox'
    'brightnessctl'
    'pipewire'
    'pipewire-pulse'
    'wireplumber'
    'yt-dlp'
    'xdotool'
    'python-requests'
    'python-psutil'
)
optdepends=(
    'ydotool: Wayland native keyboard/mouse control'
    'python-speechrecognition: Microphone voice input'
    'python-pyaudio: Microphone hardware support'
    'vosk: Offline wake-word detection (no internet needed)'
)
makedepends=('python-pip' 'python-setuptools' 'python-wheel')
conflicts=()
provides=('luna-ai')
source=("\$pkgname-\$pkgver.tar.gz::https://github.com/$GITHUB_USER/luna-ai/archive/refs/tags/v\$pkgver.tar.gz")
sha256sums=('SKIP')

prepare() {
    cd "\$srcdir"
}

package() {
    # Find source dir (GitHub extracts as luna-ai-1.0.0/)
    SRCDIR="\$srcdir/luna-ai-\$pkgver"
    [ -d "\$SRCDIR" ] || SRCDIR="\$srcdir/Luna-ai-\$pkgver"
    [ -d "\$SRCDIR" ] || SRCDIR="\$srcdir"

    # Install app files to /opt/luna-ai
    install -dm755 "\$pkgdir/opt/luna-ai"
    cp -r "\$SRCDIR"/. "\$pkgdir/opt/luna-ai/"
    rm -rf "\$pkgdir/opt/luna-ai/.git" \
           "\$pkgdir/opt/luna-ai/venv" \
           "\$pkgdir/opt/luna-ai/__pycache__" \
           "\$pkgdir/opt/luna-ai/*.tar.gz" 2>/dev/null || true

    # Install Python-only deps that are not in official repos
    install -dm755 "\$pkgdir/opt/luna-ai/vendor"
    pip install --no-deps --target="\$pkgdir/opt/luna-ai/vendor" \
        edge-tts google-genai groq 2>/dev/null || true

    # /usr/bin/luna-ai launcher
    install -dm755 "\$pkgdir/usr/bin"
    cat > "\$pkgdir/usr/bin/luna-ai" << 'BINEOF'
#!/usr/bin/env bash
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
export MOZ_ENABLE_WAYLAND=1
export QT_QPA_PLATFORM=wayland
export PYTHONPATH="/opt/luna-ai/vendor:$PYTHONPATH"
cd /opt/luna-ai
exec python /opt/luna-ai/main.py "$@"
BINEOF
    chmod 755 "\$pkgdir/usr/bin/luna-ai"

    # Desktop entry
    install -dm755 "\$pkgdir/usr/share/applications"
    cat > "\$pkgdir/usr/share/applications/luna-ai.desktop" << 'DEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Luna AI
GenericName=AI Assistant
Comment=Hacker-style AI assistant for Arch Linux + Hyprland
Exec=luna-ai
Icon=luna-ai
Terminal=false
Categories=Utility;Science;
Keywords=AI;Voice;Assistant;Luna;Hacker;
StartupWMClass=luna-ai
DEOF

    # SVG Icon
    install -dm755 "\$pkgdir/usr/share/icons/hicolor/scalable/apps"
    cat > "\$pkgdir/usr/share/icons/hicolor/scalable/apps/luna-ai.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#050510"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="#00dc8c" stroke-width="1" opacity="0.3"/>
  <circle cx="32" cy="32" r="15" fill="none" stroke="#00dc8c" stroke-width="1.5" opacity="0.6"/>
  <circle cx="32" cy="32" r="6" fill="#00dc8c" opacity="0.9"/>
  <circle cx="32" cy="32" r="3" fill="#ffffff"/>
  <line x1="32" y1="8" x2="32" y2="17" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="32" y1="47" x2="32" y2="56" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="8" y1="32" x2="17" y2="32" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="47" y1="32" x2="56" y2="32" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
</svg>
SVGEOF

    # License
    install -dm755 "\$pkgdir/usr/share/licenses/luna-ai"
    install -Dm644 "\$SRCDIR/LICENSE" "\$pkgdir/usr/share/licenses/luna-ai/LICENSE" 2>/dev/null || \
        printf 'MIT License\nCopyright (c) 2025 Arunachalam\n' > "\$pkgdir/usr/share/licenses/luna-ai/LICENSE"
}
PKGEOF

# Regenerate .SRCINFO
cd "$PKG_DIR"
makepkg --printsrcinfo > .SRCINFO 2>/dev/null || true
ok "PKGBUILD + .SRCINFO updated with correct deps"

# ══════════════════════════════════════════════
# STEP 2: Setup GitHub repository
# ══════════════════════════════════════════════
hdr "GITHUB SETUP"

cd "$DIR"

# Create LICENSE if missing
[ -f LICENSE ] || printf "MIT License\nCopyright (c) 2025 Arunachalam\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software.\n" > LICENSE

# Create README if missing
[ -f README.md ] || cat > README.md << 'READEOF'
# Luna AI

> Hacker-style AI desktop assistant for Arch Linux + Hyprland

## Features
- 🎙 Voice control with wake word ("Luna")
- 🎵 YouTube search and play via Firefox
- 🔊 Volume control (wpctl/PipeWire)
- 💡 Brightness control (brightnessctl)
- 📊 Live crypto prices, stock prices, weather
- 🤖 Gemini / Groq / Ollama AI backends
- 💻 System task engine (run commands, create files)

## Install (Arch Linux)
```bash
yay -S luna-ai
```

## Manual install
```bash
git clone https://github.com/Arunachalam-gojosaturo/luna-ai
cd luna-ai
pip install -r requirements.txt
python main.py
```

## Usage
Say **"Luna"** to wake the AI, then speak your command:
- `play Believer by Imagine Dragons`
- `volume up` / `volume 60%` / `mute`
- `brightness up` / `brightness 70%`
- `what is the BTC price`
- `weather in Chennai`
READEOF

# Init git
if [ ! -d .git ]; then
    git init
    git branch -M main
fi

# Set git identity if not set
git config user.name 2>/dev/null || git config user.name "$GITHUB_USER"
git config user.email 2>/dev/null || git config user.email "$GITHUB_USER@users.noreply.github.com"

# Stage everything
git add -A
git status --short

# Create .gitignore
cat > .gitignore << 'GIEOF'
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.tar.gz
*.zip
.DS_Store
*.egg-info/
dist/
build/
.luna_ai/
GIEOF

git add .gitignore
git commit -m "Luna AI v1.0.0 - Initial release" 2>/dev/null || \
git commit --allow-empty -m "Luna AI v1.0.0" 2>/dev/null || true

# Tag release
git tag -a v1.0.0 -m "Luna AI v1.0.0" 2>/dev/null || true

ok "Git repo initialized with v1.0.0 tag"

# ══════════════════════════════════════════════
# STEP 3: Install GitHub CLI and push
# ══════════════════════════════════════════════
hdr "PUSHING TO GITHUB"

if ! command -v gh &>/dev/null; then
    inf "Installing GitHub CLI..."
    sudo pacman -S --noconfirm github-cli
fi

if gh auth status &>/dev/null; then
    ok "GitHub CLI already authenticated"
else
    inf "Login to GitHub (browser will open)..."
    gh auth login --web
fi

# Create repo on GitHub
inf "Creating GitHub repo: $GITHUB_USER/luna-ai"
gh repo create luna-ai \
    --public \
    --description "Luna AI — Hacker-style voice AI assistant for Arch Linux + Hyprland" \
    --source="$DIR" \
    --remote=origin \
    --push 2>/dev/null || \
( git remote add origin "https://github.com/$GITHUB_USER/luna-ai.git" 2>/dev/null || \
  git remote set-url origin "https://github.com/$GITHUB_USER/luna-ai.git"
  git push -u origin main --tags )

ok "Source code live at: https://github.com/$GITHUB_USER/luna-ai"

# Push the tag too
git push origin v1.0.0 2>/dev/null || true
ok "Tag v1.0.0 pushed"

# Create GitHub release
gh release create v1.0.0 \
    --title "Luna AI v1.0.0" \
    --notes "Initial release of Luna AI — Hacker-style AI assistant for Arch Linux + Hyprland" \
    2>/dev/null || inf "Release may already exist — skipping"
ok "GitHub release created"

# ══════════════════════════════════════════════
# STEP 4: Submit to AUR
# ══════════════════════════════════════════════
hdr "SUBMITTING TO AUR"

cd "$PKG_DIR"

# Update PKGBUILD with correct GitHub URL (replace 'yourusername')
sed -i "s|yourusername|$GITHUB_USER|g" PKGBUILD .SRCINFO 2>/dev/null || true

# Regenerate .SRCINFO with final URLs
makepkg --printsrcinfo > .SRCINFO 2>/dev/null || true

# SSH key setup
if [ ! -f ~/.ssh/id_ed25519 ]; then
    inf "Generating SSH key for AUR..."
    ssh-keygen -t ed25519 -C "$GITHUB_USER@aur" -f ~/.ssh/id_ed25519 -N ""
    echo ""
    echo -e "  ${YLW}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "  ${YLW}║  ADD THIS SSH KEY TO YOUR AUR ACCOUNT:          ║${NC}"
    echo -e "  ${YLW}║  https://aur.archlinux.org/account              ║${NC}"
    echo -e "  ${YLW}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo -e "  ${YLW}Copy the key above, paste it in AUR → My Account → SSH Keys${NC}"
    echo -e "  ${YLW}Then press ENTER to continue...${NC}"
    read -r
else
    ok "SSH key exists: ~/.ssh/id_ed25519"
fi

# Add AUR to known hosts
ssh-keyscan aur.archlinux.org >> ~/.ssh/known_hosts 2>/dev/null
ok "AUR host key added"

# Init AUR git repo
if [ ! -d "$PKG_DIR/.git" ]; then
    cd "$PKG_DIR"
    git init
    git remote add origin ssh://aur@aur.archlinux.org/luna-ai.git
fi

git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_USER@users.noreply.github.com"

# Try to fetch existing AUR package (in case it already exists)
git fetch origin 2>/dev/null || true
git checkout -b master 2>/dev/null || git checkout master 2>/dev/null || true

cd "$PKG_DIR"
git add PKGBUILD .SRCINFO LICENSE
git commit -m "Luna AI v1.0.0 - Initial AUR release" 2>/dev/null || true

inf "Pushing to AUR..."
if git push -u origin master 2>&1; then
    echo ""
    echo -e "  ${GRN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "  ${GRN}║  🎉 LUNA AI IS NOW ON THE AUR!                 ║${NC}"
    echo -e "  ${GRN}║                                                ║${NC}"
    echo -e "  ${GRN}║  Install with:  yay -S luna-ai                 ║${NC}"
    echo -e "  ${GRN}║  AUR page: https://aur.archlinux.org/packages/luna-ai ║${NC}"
    echo -e "  ${GRN}╚══════════════════════════════════════════════════╝${NC}"
else
    err "AUR push failed. Most likely the SSH key is not added to AUR yet."
    echo ""
    echo -e "  ${YLW}Manual steps:${NC}"
    echo "  1. Go to https://aur.archlinux.org/account"
    echo "  2. Paste this SSH public key:"
    echo ""
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "  3. Then run:"
    echo "     cd ~/aur-luna-ai"
    echo "     git push -u origin master"
fi
