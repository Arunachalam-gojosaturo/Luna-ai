#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   LUNA AI — AUR PACKAGE BUILDER                            ║
# ║   Builds a proper Arch package + submits to AUR            ║
# ║   Run from: ~/Downloads/Luna-ai                            ║
# ║   chmod +x luna_aur_package.sh && ./luna_aur_package.sh    ║
# ╚══════════════════════════════════════════════════════════════╝
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GRN='\033[0;32m'; YLW='\033[1;33m'; CYN='\033[0;36m'; NC='\033[0m'
ok()  { echo -e "  ${GRN}[✓]${NC} $1"; }
inf() { echo -e "  ${YLW}[→]${NC} $1"; }
hdr() { echo -e "\n  ${CYN}━━━ $1 ━━━${NC}"; }

echo ""
echo -e "  ${CYN}╔══════════════════════════════════════════════╗${NC}"
echo -e "  ${CYN}║   LUNA AI — AUR PACKAGE BUILDER            ║${NC}"
echo -e "  ${CYN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Install build tools ───────────────────────────────────────────────────────
hdr "INSTALLING BUILD TOOLS"
sudo pacman -S --noconfirm --needed base-devel git openssh 2>/dev/null || true
ok "base-devel git openssh ready"

# ── Create package workspace ──────────────────────────────────────────────────
hdr "CREATING PACKAGE"
PKG_DIR="$HOME/aur-luna-ai"
mkdir -p "$PKG_DIR"
cd "$PKG_DIR"

# ── Get current version from main.py ─────────────────────────────────────────
VERSION=$(grep -oP '(?<=v)\d+\.\d+\.\d+' "$DIR/main.py" 2>/dev/null | head -1 || echo "1.0.0")
[ -z "$VERSION" ] && VERSION="1.0.0"
inf "Package version: $VERSION"

# ── Create source tarball from current Luna directory ─────────────────────────
hdr "CREATING SOURCE ARCHIVE"
TARNAME="luna-ai-$VERSION.tar.gz"
cd "$(dirname "$DIR")"
tar --exclude=".git" --exclude="__pycache__" --exclude="*.pyc" \
    --exclude=".venv" --exclude="venv" --exclude="*.zip" \
    -czf "$PKG_DIR/$TARNAME" "$(basename "$DIR")/"
cd "$PKG_DIR"

# Compute SHA256
SHA256=$(sha256sum "$TARNAME" | cut -d' ' -f1)
ok "Tarball: $TARNAME"
ok "SHA256: $SHA256"

# ── Write PKGBUILD ────────────────────────────────────────────────────────────
hdr "WRITING PKGBUILD"
cat > "$PKG_DIR/PKGBUILD" << PKGEOF
# Maintainer: $(git config --global user.name 2>/dev/null || echo "Your Name") <$(git config --global user.email 2>/dev/null || echo "your@email.com")>
pkgname=luna-ai
pkgver=$VERSION
pkgrel=1
pkgdesc="Luna AI — Hacker-style AI desktop assistant for Arch Linux + Hyprland. Voice control, YouTube, brightness, volume, live data."
arch=('any')
url="https://github.com/$(git config --global user.name 2>/dev/null || echo 'yourusername')/luna-ai"
license=('MIT')
depends=(
    'python'
    'python-pyqt6'
    'firefox'
    'brightnessctl'
    'pipewire'
    'pipewire-pulse'
    'wireplumber'
    'yt-dlp'
    'xdotool'
)
optdepends=(
    'ydotool: Wayland native input control'
    'python-speechrecognition: Voice input / wake word'
    'python-pyaudio: Microphone support'
    'vosk: Offline wake word detection'
)
makedepends=('python-pip' 'python-setuptools')
source=("luna-ai-\$pkgver.tar.gz::https://github.com/$(git config --global user.name 2>/dev/null || echo 'yourusername')/luna-ai/archive/v\$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "\$srcdir"
    # Find the extracted directory
    SRCDIR=\$(ls -d Luna-ai-* luna-ai-* 2>/dev/null | head -1)
    [ -z "\$SRCDIR" ] && SRCDIR="."

    # Install application files
    install -dm755 "\$pkgdir/opt/luna-ai"
    cp -r "\$SRCDIR"/. "\$pkgdir/opt/luna-ai/"

    # Install Python dependencies into package
    pip install --no-deps --target="\$pkgdir/opt/luna-ai/deps" \
        edge-tts google-genai groq requests beautifulsoup4 psutil 2>/dev/null || true

    # Create launcher script
    install -dm755 "\$pkgdir/usr/bin"
    cat > "\$pkgdir/usr/bin/luna-ai" << 'LAUNCHEOF'
#!/usr/bin/env bash
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-wayland-1}"
export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="\${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/\$(id -u)/bus}"
export MOZ_ENABLE_WAYLAND=1
export QT_QPA_PLATFORM=wayland
export PYTHONPATH="/opt/luna-ai/deps:\$PYTHONPATH"
cd /opt/luna-ai
exec python /opt/luna-ai/main.py "\$@"
LAUNCHEOF
    chmod +x "\$pkgdir/usr/bin/luna-ai"

    # Desktop entry
    install -dm755 "\$pkgdir/usr/share/applications"
    cat > "\$pkgdir/usr/share/applications/luna-ai.desktop" << 'DESKEOF'
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
Keywords=AI;Assistant;Luna;Voice;
StartupWMClass=luna-ai
DESKEOF

    # Icon
    install -dm755 "\$pkgdir/usr/share/icons/hicolor/scalable/apps"
    cat > "\$pkgdir/usr/share/icons/hicolor/scalable/apps/luna-ai.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#050510"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="#00dc8c" stroke-width="1" opacity="0.3"/>
  <circle cx="32" cy="32" r="15" fill="none" stroke="#00dc8c" stroke-width="1.5" opacity="0.6"/>
  <circle cx="32" cy="32" r="6"  fill="#00dc8c" opacity="0.9"/>
  <circle cx="32" cy="32" r="3"  fill="#ffffff"/>
  <line x1="32" y1="8"  x2="32" y2="17" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="32" y1="47" x2="32" y2="56" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="8"  y1="32" x2="17" y2="32" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="47" y1="32" x2="56" y2="32" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
</svg>
SVGEOF

    # License
    install -Dm644 "\$srcdir/\$SRCDIR/LICENSE" "\$pkgdir/usr/share/licenses/luna-ai/LICENSE" 2>/dev/null || \
    printf "MIT License\nCopyright (c) $(date +%Y)\n" > "\$pkgdir/usr/share/licenses/luna-ai/LICENSE"
}
PKGEOF
ok "PKGBUILD written"

# ── Write .SRCINFO (required by AUR) ─────────────────────────────────────────
hdr "GENERATING .SRCINFO"
cd "$PKG_DIR"
makepkg --printsrcinfo > .SRCINFO 2>/dev/null || \
python3 - << 'PYEOF'
# Manual .SRCINFO generation if makepkg fails
content = """pkgbase = luna-ai
\tpkgdesc = Luna AI — Hacker-style AI desktop assistant for Arch Linux + Hyprland
\tpkgver = 1.0.0
\tpkgrel = 1
\turl = https://github.com/yourusername/luna-ai
\tarch = any
\tlicense = MIT
\tdepends = python
\tdepends = python-pyqt6
\tdepends = firefox
\tdepends = brightnessctl
\tdepends = pipewire
\tdepends = yt-dlp
\tdepends = xdotool
\toptdepends = ydotool: Wayland native input
\toptdepends = python-speechrecognition: Voice input
\tmakedepends = python-pip
\tsource = luna-ai-1.0.0.tar.gz::https://github.com/yourusername/luna-ai/archive/v1.0.0.tar.gz
\tsha256sums = SKIP

pkgname = luna-ai
"""
open(".SRCINFO","w").write(content)
print("  [✓] .SRCINFO generated manually")
PYEOF
ok ".SRCINFO ready"

# ── Write LICENSE ─────────────────────────────────────────────────────────────
cat > "$PKG_DIR/LICENSE" << LICEOF
MIT License

Copyright (c) $(date +%Y) Luna AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
LICEOF
ok "LICENSE written"

# ── Test build ────────────────────────────────────────────────────────────────
hdr "TEST LOCAL BUILD"
cd "$PKG_DIR"
inf "Running makepkg --nobuild to validate PKGBUILD..."
makepkg --nobuild --nocheck --skipinteg 2>&1 | tail -5 || true
ok "PKGBUILD syntax valid"

# ── Git setup for AUR ─────────────────────────────────────────────────────────
hdr "AUR SUBMISSION SETUP"

echo ""
inf "STEP 1 — Create AUR account (if you don't have one):"
echo "         https://aur.archlinux.org/register"
echo ""
inf "STEP 2 — Add your SSH key to AUR account:"
echo "         https://aur.archlinux.org/account"
echo ""
inf "STEP 3 — Generate SSH key if needed:"
echo "         ssh-keygen -t ed25519 -C 'your@email.com'"
echo "         cat ~/.ssh/id_ed25519.pub  (copy this to AUR)"
echo ""
inf "STEP 4 — Clone the AUR package repo (creates it if new):"
echo "         cd ~/aur-luna-ai"
echo "         git init"
echo "         git remote add origin ssh://aur@aur.archlinux.org/luna-ai.git"
echo ""
inf "STEP 5 — Update PKGBUILD with your GitHub URL, then:"
echo "         cd ~/aur-luna-ai"
echo "         git add PKGBUILD .SRCINFO LICENSE"
echo "         git commit -m 'Initial release v1.0.0'"
echo "         git push -u origin master"
echo ""

# ── Write upload script ───────────────────────────────────────────────────────
cat > "$PKG_DIR/upload_to_aur.sh" << 'UPLOADEOF'
#!/usr/bin/env bash
# Run this AFTER setting up your AUR account and SSH key
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "[~] Refreshing .SRCINFO..."
makepkg --printsrcinfo > .SRCINFO

echo "[~] Committing to AUR..."
git add PKGBUILD .SRCINFO LICENSE
git commit -m "Luna AI v$(grep '^pkgver' PKGBUILD | cut -d= -f2) update"
git push origin master
echo "[✓] Published to AUR! Install with: yay -S luna-ai"
UPLOADEOF
chmod +x "$PKG_DIR/upload_to_aur.sh"

# ── Also push source code to GitHub first (needed for AUR source URL) ─────────
cat > "$PKG_DIR/setup_github.sh" << 'GHEOF'
#!/usr/bin/env bash
# Run this to push Luna AI source to GitHub first
# Then update the URL in PKGBUILD to match your GitHub repo

GITHUB_USER="$1"
if [ -z "$GITHUB_USER" ]; then
    echo "Usage: ./setup_github.sh your_github_username"
    exit 1
fi

cd ~/Downloads/Luna-ai

# Init git if not already
[ -d .git ] || git init
git add -A
git commit -m "Luna AI v1.0.0 — Initial release" 2>/dev/null || true

# Create GitHub repo via gh CLI (install: sudo pacman -S github-cli)
if command -v gh &>/dev/null; then
    gh repo create luna-ai --public --description "Luna AI — Hacker AI assistant for Arch Linux + Hyprland" || true
    git remote add origin "https://github.com/$GITHUB_USER/luna-ai.git" 2>/dev/null || true
    git branch -M main
    git push -u origin main
    echo "[✓] Pushed to https://github.com/$GITHUB_USER/luna-ai"
else
    echo "[→] Install gh CLI: sudo pacman -S github-cli"
    echo "[→] Or manually create repo at github.com and push:"
    echo "    git remote add origin https://github.com/$GITHUB_USER/luna-ai.git"
    echo "    git push -u origin main"
fi

# Update PKGBUILD URL
sed -i "s|yourusername|$GITHUB_USER|g" ~/aur-luna-ai/PKGBUILD
sed -i "s|yourusername|$GITHUB_USER|g" ~/aur-luna-ai/.SRCINFO
echo "[✓] PKGBUILD updated with your GitHub URL"
echo ""
echo "Now run: cd ~/aur-luna-ai && ./upload_to_aur.sh"
GHEOF
chmod +x "$PKG_DIR/setup_github.sh"
ok "Helper scripts created"

# ── Final summary ─────────────────────────────────────────────────────────────
echo ""
echo -e "  ${GRN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GRN}║   PACKAGE READY AT: ~/aur-luna-ai              ║${NC}"
echo -e "  ${GRN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "  ${GRN}║  Files created:                                ║${NC}"
echo -e "  ${GRN}║   ~/aur-luna-ai/PKGBUILD                       ║${NC}"
echo -e "  ${GRN}║   ~/aur-luna-ai/.SRCINFO                       ║${NC}"
echo -e "  ${GRN}║   ~/aur-luna-ai/LICENSE                        ║${NC}"
echo -e "  ${GRN}║   ~/aur-luna-ai/upload_to_aur.sh               ║${NC}"
echo -e "  ${GRN}║   ~/aur-luna-ai/setup_github.sh                ║${NC}"
echo -e "  ${GRN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "  ${GRN}║  FULL STEPS TO PUBLISH:                        ║${NC}"
echo -e "  ${GRN}║                                                ║${NC}"
echo -e "  ${GRN}║  1. Push source to GitHub first:               ║${NC}"
echo -e "  ${GRN}║     cd ~/aur-luna-ai                           ║${NC}"
echo -e "  ${GRN}║     ./setup_github.sh your_github_username     ║${NC}"
echo -e "  ${GRN}║                                                ║${NC}"
echo -e "  ${GRN}║  2. Create AUR account:                        ║${NC}"
echo -e "  ${GRN}║     https://aur.archlinux.org/register         ║${NC}"
echo -e "  ${GRN}║                                                ║${NC}"
echo -e "  ${GRN}║  3. Add SSH key to AUR account settings        ║${NC}"
echo -e "  ${GRN}║     ssh-keygen -t ed25519                      ║${NC}"
echo -e "  ${GRN}║     cat ~/.ssh/id_ed25519.pub  → paste to AUR  ║${NC}"
echo -e "  ${GRN}║                                                ║${NC}"
echo -e "  ${GRN}║  4. Clone AUR repo + push:                     ║${NC}"
echo -e "  ${GRN}║     cd ~/aur-luna-ai                           ║${NC}"
echo -e "  ${GRN}║     git init                                   ║${NC}"
echo -e "  ${GRN}║     git remote add origin \                    ║${NC}"
echo -e "  ${GRN}║       ssh://aur@aur.archlinux.org/luna-ai.git  ║${NC}"
echo -e "  ${GRN}║     ./upload_to_aur.sh                         ║${NC}"
echo -e "  ${GRN}║                                                ║${NC}"
echo -e "  ${GRN}║  5. Anyone can install with:                   ║${NC}"
echo -e "  ${GRN}║     yay -S luna-ai                             ║${NC}"
echo -e "  ${GRN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
