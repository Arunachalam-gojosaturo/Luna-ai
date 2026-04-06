#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  LUNA AI v6 — AUR Package Builder                                  ║
# ║  Builds PKGBUILD + submits to AUR                                  ║
# ║  After publish:  yay -S luna-ai                                    ║
# ║  To update:      ./luna_aur_package.sh --bump 6.1.0                ║
# ╚══════════════════════════════════════════════════════════════════════╝
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$HOME/aur-luna-ai"

GRN='\033[0;32m'; YLW='\033[1;33m'; CYN='\033[0;36m'; BLD='\033[1m'; NC='\033[0m'
ok()  { echo -e "  ${GRN}[✓]${NC} $1"; }
inf() { echo -e "  ${YLW}[→]${NC} $1"; }
hdr() { echo -e "\n  ${CYN}${BLD}━━━ $1 ━━━${NC}"; }

echo -e "\n  ${CYN}${BLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "  ${CYN}${BLD}║   LUNA AI v6 — AUR PACKAGE BUILDER         ║${NC}"
echo -e "  ${CYN}${BLD}╚══════════════════════════════════════════════╝${NC}\n"

# ── Handle --bump flag ────────────────────────────────────────────────────────
if [[ "${1:-}" == "--bump" && -n "${2:-}" ]]; then
    NEW_VER="$2"
    hdr "BUMPING VERSION TO $NEW_VER"
    cd "$PKG_DIR"
    sed -i "s/^pkgver=.*/pkgver=$NEW_VER/" PKGBUILD
    sed -i "s/^pkgrel=.*/pkgrel=1/"       PKGBUILD
    SRC_LINE=$(grep '^source=' PKGBUILD | head -1)
    TAR_URL=$(echo "$SRC_LINE" | grep -oP 'https://[^"]+' | head -1 | sed "s/\\\$pkgver/$NEW_VER/g")
    inf "Fetching SHA256 for $TAR_URL..."
    NEW_SHA=$(curl -sL "$TAR_URL" | sha256sum | cut -d' ' -f1)
    sed -i "s/sha256sums=.*/sha256sums=('$NEW_SHA')/" PKGBUILD
    makepkg --printsrcinfo > .SRCINFO
    git add PKGBUILD .SRCINFO
    git commit -m "Update to v$NEW_VER"
    git push origin master
    ok "AUR updated to v$NEW_VER — users: yay -Syu"
    exit 0
fi

# ── Gather info ───────────────────────────────────────────────────────────────
hdr "PACKAGE INFO"
sudo pacman -S --noconfirm --needed base-devel git openssh 2>/dev/null || true
MAINT_NAME=$(git config --global user.name  2>/dev/null || echo "Your Name")
MAINT_EMAIL=$(git config --global user.email 2>/dev/null || echo "your@email.com")

read -rp "  GitHub username: " GITHUB_USER
REPO_NAME="luna-ai"
VERSION="6.0.0"
REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME"
mkdir -p "$PKG_DIR"

inf "Repo: $REPO_URL  |  Version: $VERSION"

# ── Push to GitHub ────────────────────────────────────────────────────────────
hdr "PUSHING TO GITHUB"
cd "$DIR"
[ -d .git ] || git init
git config user.name  "$MAINT_NAME"
git config user.email "$MAINT_EMAIL"
git add -A
git commit -m "Luna AI v$VERSION" 2>/dev/null || true
git tag -a "v$VERSION" -m "v$VERSION" 2>/dev/null || true
git remote get-url origin &>/dev/null \
    && git remote set-url origin "$REPO_URL" \
    || git remote add origin "$REPO_URL"
git push origin main --tags 2>/dev/null \
    || git push origin master --tags 2>/dev/null \
    || inf "Push failed — check credentials. Continue anyway."
ok "Source at $REPO_URL"

# ── SHA256 ────────────────────────────────────────────────────────────────────
hdr "COMPUTING SHA256"
TAR_URL="https://github.com/$GITHUB_USER/$REPO_NAME/archive/refs/tags/v$VERSION.tar.gz"
SHA256=$(curl -sL "$TAR_URL" | sha256sum | cut -d' ' -f1 2>/dev/null || echo "SKIP")
ok "SHA256: $SHA256"

# ── Write PKGBUILD ────────────────────────────────────────────────────────────
hdr "WRITING PKGBUILD"
cat > "$PKG_DIR/PKGBUILD" << PKGEOF
# Maintainer: $MAINT_NAME <$MAINT_EMAIL>
pkgname=luna-ai
pkgver=$VERSION
pkgrel=1
pkgdesc="Luna AI v6 — Hacker-style voice AI desktop assistant. Voice, YouTube, brightness, crypto, live data."
arch=('any')
url="$REPO_URL"
license=('MIT')

depends=(
    'python>=3.10'
    'python-pyqt6'
    'mpv'
    'python-pip'
)
optdepends=(
    'ffmpeg: ffplay audio fallback'
    'python-pygame: pygame audio fallback'
    'brightnessctl: screen brightness control'
    'yt-dlp: YouTube music playback'
    'xdotool: X11 keyboard/mouse control'
    'ydotool: Wayland keyboard/mouse control'
    'python-speechrecognition: voice input'
    'python-pyaudio: microphone support'
)
makedepends=('python-pip')

source=("luna-ai-\$pkgver.tar.gz::https://github.com/$GITHUB_USER/$REPO_NAME/archive/v\$pkgver.tar.gz")
sha256sums=('$SHA256')

package() {
    local SRCDIR
    SRCDIR=\$(find "\$srcdir" -maxdepth 1 -mindepth 1 -type d | head -1)

    install -dm755 "\$pkgdir/opt/luna-ai"
    cp -r "\$SRCDIR"/. "\$pkgdir/opt/luna-ai/"

    # Install Python deps into app directory
    TMPDIR=/tmp pip install --no-deps --quiet \
        --target="\$pkgdir/opt/luna-ai/deps" \
        edge-tts google-genai groq requests \
        beautifulsoup4 psutil pygame 2>/dev/null || true

    # Global launcher
    install -dm755 "\$pkgdir/usr/bin"
    cat > "\$pkgdir/usr/bin/luna-ai" << 'LAUNCHEOF'
#!/usr/bin/env bash
export DISPLAY="\${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-wayland-1}"
export QT_QPA_PLATFORM="\${QT_QPA_PLATFORM:-wayland}"
export MOZ_ENABLE_WAYLAND=1
export TMPDIR=/tmp
PYTHONPATH="/opt/luna-ai/deps:\$PYTHONPATH" exec python /opt/luna-ai/main.py "\$@"
LAUNCHEOF
    chmod +x "\$pkgdir/usr/bin/luna-ai"

    install -dm755 "\$pkgdir/usr/share/applications"
    cat > "\$pkgdir/usr/share/applications/luna-ai.desktop" << 'DESKTOPEOF'
[Desktop Entry]
Name=Luna AI
Comment=Hacker AI assistant with voice control
Exec=luna-ai
Terminal=false
Type=Application
Categories=Utility;AI;
DESKTOPEOF

    install -Dm644 "\$SRCDIR/LICENSE" "\$pkgdir/usr/share/licenses/luna-ai/LICENSE" 2>/dev/null || true
}
PKGEOF
ok "PKGBUILD written"

cd "$PKG_DIR"
makepkg --printsrcinfo > .SRCINFO 2>/dev/null || true
ok ".SRCINFO generated"

echo ""
echo -e "  ${GRN}${BLD}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "  ${GRN}${BLD}║   NEXT STEPS TO PUBLISH TO AUR                       ║${NC}"
echo -e "  ${GRN}${BLD}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "  ${GRN}${BLD}║                                                      ║${NC}"
echo -e "  ${GRN}${BLD}║  1. Register at: https://aur.archlinux.org/register  ║${NC}"
echo -e "  ${GRN}${BLD}║                                                      ║${NC}"
echo -e "  ${GRN}${BLD}║  2. Add SSH key to AUR account settings              ║${NC}"
echo -e "  ${GRN}${BLD}║     ssh-keygen -t ed25519                            ║${NC}"
echo -e "  ${GRN}${BLD}║     cat ~/.ssh/id_ed25519.pub  → paste to AUR        ║${NC}"
echo -e "  ${GRN}${BLD}║                                                      ║${NC}"
echo -e "  ${GRN}${BLD}║  3. Init AUR repo and push:                          ║${NC}"
echo -e "  ${GRN}${BLD}║     cd ~/aur-luna-ai                                 ║${NC}"
echo -e "  ${GRN}${BLD}║     git init                                         ║${NC}"
echo -e "  ${GRN}${BLD}║     git remote add origin \\                          ║${NC}"
echo -e "  ${GRN}${BLD}║       ssh://aur@aur.archlinux.org/luna-ai.git        ║${NC}"
echo -e "  ${GRN}${BLD}║     git add PKGBUILD .SRCINFO                        ║${NC}"
echo -e "  ${GRN}${BLD}║     git commit -m 'Initial release v6.0.0'           ║${NC}"
echo -e "  ${GRN}${BLD}║     git push -u origin master                        ║${NC}"
echo -e "  ${GRN}${BLD}║                                                      ║${NC}"
echo -e "  ${GRN}${BLD}║  4. Anyone installs with:  yay -S luna-ai            ║${NC}"
echo -e "  ${GRN}${BLD}║                                                      ║${NC}"
echo -e "  ${GRN}${BLD}║  5. Push an update (new GitHub tag first):           ║${NC}"
echo -e "  ${GRN}${BLD}║     bash luna_aur_package.sh --bump 6.1.0            ║${NC}"
echo -e "  ${GRN}${BLD}║     Users update with:  yay -Syu                     ║${NC}"
echo -e "  ${GRN}${BLD}║                                                      ║${NC}"
echo -e "  ${GRN}${BLD}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
