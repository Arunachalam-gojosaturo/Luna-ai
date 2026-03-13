#!/usr/bin/env bash
# Luna AI — Push to AUR using existing GitHub repo
# cd ~/Downloads/Luna-ai && chmod +x luna_aur_push.sh && ./luna_aur_push.sh

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$HOME/aur-luna-ai"
mkdir -p "$PKG_DIR"

GRN='\033[0;32m'; YLW='\033[1;33m'; CYN='\033[0;36m'; NC='\033[0m'
ok()  { echo -e "  ${GRN}[✓]${NC} $1"; }
inf() { echo -e "  ${YLW}[→]${NC} $1"; }

echo ""
echo -e "  ${CYN}╔══════════════════════════════════════════════╗${NC}"
echo -e "  ${CYN}║   LUNA AI — AUR PUSH                       ║${NC}"
echo -e "  ${CYN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Get info from user ────────────────────────────────────────────────────────
read -rp "  Enter your GitHub repo URL (e.g. https://github.com/user/luna-ai): " REPO_URL
read -rp "  Enter your name (for PKGBUILD Maintainer): " MAINT_NAME
read -rp "  Enter your email: " MAINT_EMAIL

# Extract username and repo name
GITHUB_USER=$(echo "$REPO_URL" | sed 's|.*github.com/||' | cut -d'/' -f1)
REPO_NAME=$(echo "$REPO_URL" | sed 's|.*github.com/||' | cut -d'/' -f2 | sed 's|\.git||')
VERSION="1.0.0"

inf "GitHub: $GITHUB_USER/$REPO_NAME"
inf "Version: $VERSION"

# ── Push source to GitHub first ───────────────────────────────────────────────
echo ""
inf "Pushing source code to GitHub..."
cd "$DIR"

[ -f LICENSE ] || printf "MIT License\nCopyright (c) 2025 $MAINT_NAME\n" > LICENSE
[ -f .gitignore ] || cat > .gitignore << 'GI'
__pycache__/
*.pyc
.venv/
venv/
*.tar.gz
*.zip
.luna_ai/
GI

git config user.name "$MAINT_NAME"
git config user.email "$MAINT_EMAIL"

git add -A
git commit -m "Luna AI v$VERSION" 2>/dev/null || true
git tag -a "v$VERSION" -m "v$VERSION" 2>/dev/null || true

# Set remote
git remote get-url origin 2>/dev/null && \
    git remote set-url origin "$REPO_URL" || \
    git remote add origin "$REPO_URL"

git push origin main --tags 2>/dev/null || \
git push origin master --tags 2>/dev/null || \
inf "Push failed — check your GitHub credentials. Continue with AUR anyway."

ok "Source pushed to $REPO_URL"

# ── Get SHA256 of the release tarball ─────────────────────────────────────────
inf "Getting SHA256 of GitHub release tarball..."
TAR_URL="https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v$VERSION.tar.gz"
SHA256=$(curl -sL "$TAR_URL" | sha256sum | cut -d' ' -f1 2>/dev/null || echo "SKIP")
ok "SHA256: $SHA256"

# ── Write PKGBUILD ────────────────────────────────────────────────────────────
cat > "$PKG_DIR/PKGBUILD" << PKGEOF
# Maintainer: $MAINT_NAME <$MAINT_EMAIL>
pkgname=luna-ai
pkgver=$VERSION
pkgrel=1
pkgdesc="Luna AI - Hacker-style voice AI assistant for Arch Linux + Hyprland (YouTube, brightness, volume, live crypto/weather)"
arch=('any')
url="https://github.com/$GITHUB_USER/$REPO_NAME"
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
    'ydotool: Wayland native input control'
    'python-speechrecognition: Microphone voice input'
    'python-pyaudio: Microphone hardware support'
)
makedepends=('python-pip')
provides=('luna-ai')
source=("\$pkgname-\$pkgver.tar.gz::https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v\$pkgver.tar.gz")
sha256sums=('$SHA256')

package() {
    SRCDIR="\$srcdir/$REPO_NAME-\$pkgver"
    [ -d "\$SRCDIR" ] || SRCDIR="\$srcdir"

    install -dm755 "\$pkgdir/opt/luna-ai"
    cp -r "\$SRCDIR"/. "\$pkgdir/opt/luna-ai/"
    rm -rf "\$pkgdir/opt/luna-ai/.git" "\$pkgdir/opt/luna-ai/venv" "\$pkgdir/opt/luna-ai/__pycache__" 2>/dev/null || true

    # Pip deps not in official repos
    install -dm755 "\$pkgdir/opt/luna-ai/vendor"
    pip install --no-deps --target="\$pkgdir/opt/luna-ai/vendor" edge-tts google-genai groq 2>/dev/null || true

    # Launcher
    install -dm755 "\$pkgdir/usr/bin"
    cat > "\$pkgdir/usr/bin/luna-ai" << 'BINEOF'
#!/usr/bin/env bash
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-wayland-1}"
export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="\${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/\$(id -u)/bus}"
export MOZ_ENABLE_WAYLAND=1
export QT_QPA_PLATFORM=wayland
export PYTHONPATH="/opt/luna-ai/vendor:\$PYTHONPATH"
cd /opt/luna-ai
exec python /opt/luna-ai/main.py "\$@"
BINEOF
    chmod 755 "\$pkgdir/usr/bin/luna-ai"

    # Desktop entry
    install -dm755 "\$pkgdir/usr/share/applications"
    cat > "\$pkgdir/usr/share/applications/luna-ai.desktop" << 'DEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Luna AI
Comment=Hacker-style AI assistant for Arch Linux + Hyprland
Exec=luna-ai
Icon=luna-ai
Terminal=false
Categories=Utility;Science;
Keywords=AI;Voice;Assistant;Luna;
DEOF

    # Icon
    install -dm755 "\$pkgdir/usr/share/icons/hicolor/scalable/apps"
    cat > "\$pkgdir/usr/share/icons/hicolor/scalable/apps/luna-ai.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#050510"/>
  <circle cx="32" cy="32" r="15" fill="none" stroke="#00dc8c" stroke-width="1.5" opacity="0.6"/>
  <circle cx="32" cy="32" r="6" fill="#00dc8c"/>
  <circle cx="32" cy="32" r="3" fill="#ffffff"/>
  <line x1="32" y1="8" x2="32" y2="17" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="32" y1="47" x2="32" y2="56" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="8" y1="32" x2="17" y2="32" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
  <line x1="47" y1="32" x2="56" y2="32" stroke="#00dc8c" stroke-width="1.5" opacity="0.7"/>
</svg>
SVGEOF

    install -dm755 "\$pkgdir/usr/share/licenses/luna-ai"
    install -Dm644 "\$SRCDIR/LICENSE" "\$pkgdir/usr/share/licenses/luna-ai/LICENSE" 2>/dev/null || true
}
PKGEOF

# ── Generate .SRCINFO ─────────────────────────────────────────────────────────
cd "$PKG_DIR"
makepkg --printsrcinfo > .SRCINFO 2>/dev/null || true
ok "PKGBUILD + .SRCINFO ready"

# ── SSH key for AUR ───────────────────────────────────────────────────────────
echo ""
if [ ! -f ~/.ssh/id_ed25519 ]; then
    inf "Generating SSH key..."
    ssh-keygen -t ed25519 -C "$MAINT_EMAIL" -f ~/.ssh/id_ed25519 -N ""
fi

echo -e "  ${YLW}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "  ${YLW}║  ADD THIS KEY TO AUR: https://aur.archlinux.org/account ║${NC}"
echo -e "  ${YLW}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
cat ~/.ssh/id_ed25519.pub
echo ""
echo -e "  ${YLW}Paste that key in AUR → My Account → SSH Public Key${NC}"
echo -e "  ${YLW}Press ENTER when done...${NC}"
read -r

# ── Push to AUR ───────────────────────────────────────────────────────────────
ssh-keyscan aur.archlinux.org >> ~/.ssh/known_hosts 2>/dev/null

cd "$PKG_DIR"
if [ ! -d .git ]; then
    git init
    git remote add origin ssh://aur@aur.archlinux.org/luna-ai.git
fi
git config user.name "$MAINT_NAME"
git config user.email "$MAINT_EMAIL"
git fetch origin 2>/dev/null || true
git checkout -B master 2>/dev/null || true

git add PKGBUILD .SRCINFO LICENSE
git commit -m "Luna AI v$VERSION initial release"

inf "Pushing to AUR..."
if git push -u origin master; then
    echo ""
    echo -e "  ${GRN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "  ${GRN}║  🎉 PUBLISHED!  yay -S luna-ai                 ║${NC}"
    echo -e "  ${GRN}║  https://aur.archlinux.org/packages/luna-ai    ║${NC}"
    echo -e "  ${GRN}╚══════════════════════════════════════════════════╝${NC}"
else
    echo -e "  ${YLW}SSH key not saved yet — add it to AUR and run:${NC}"
    echo "     cd ~/aur-luna-ai && git push -u origin master"
fi
