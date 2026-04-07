#!/usr/bin/env bash
set -e

# ===== CONFIG =====
PROJECT_DIR="$HOME/Downloads/luna-ai-v6"
AUR_DIR="$HOME/aur-luna-ai"
PKGNAME="luna-ai"
GITHUB_REPO="https://github.com/Arunachalam-gojosaturo/Luna-ai"

VERSION="$1"

# ===== VALIDATION =====
if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh 6.2.0"
    exit 1
fi

echo "======================================"
echo "🚀 Releasing version v$VERSION"
echo "======================================"

# ===== STEP 1: GITHUB =====
echo "==> Updating GitHub..."

cd "$PROJECT_DIR"

git add . || true
git commit -m "Release v$VERSION" || true

# create tag safely
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "Tag v$VERSION already exists"
else
    git tag "v$VERSION"
fi

git push
git push origin "v$VERSION"

echo "==> GitHub updated"

# ===== STEP 2: VERIFY TAG EXISTS =====
echo "==> Verifying GitHub tag..."

TAR_URL="$GITHUB_REPO/archive/refs/tags/v$VERSION.tar.gz"

if curl --head --silent --fail "$TAR_URL" >/dev/null; then
    echo "✔ Tag archive exists"
else
    echo "❌ ERROR: GitHub tag not available!"
    echo "Check: $TAR_URL"
    exit 1
fi

# ===== STEP 3: UPDATE AUR =====
echo "==> Updating AUR..."

cd "$AUR_DIR"

# update pkgver
sed -i "s/^pkgver=.*/pkgver=$VERSION/" PKGBUILD

# reset pkgrel
sed -i "s/^pkgrel=.*/pkgrel=1/" PKGBUILD

# fix source URL automatically
sed -i "s|source=.*|source=(\"$PKGNAME-\$pkgver.tar.gz::$GITHUB_REPO/archive/refs/tags/v\$pkgver.tar.gz\")|" PKGBUILD

# regenerate SRCINFO
makepkg --printsrcinfo > .SRCINFO

# ===== STEP 4: VALIDATE PKGBUILD =====
echo "==> Validating PKGBUILD..."

if ! bash -n PKGBUILD; then
    echo "❌ PKGBUILD syntax error"
    exit 1
fi

if grep -q '<<<<<<<\|=======\|>>>>>>>' PKGBUILD .SRCINFO; then
    echo "❌ Merge conflict markers found!"
    exit 1
fi

# ===== STEP 5: COMMIT AUR =====
git add PKGBUILD .SRCINFO
git commit -m "Update to v$VERSION" || true
git push

echo "==> AUR updated"

# ===== STEP 6: LOCAL CLEANUP =====
echo "==> Cleaning local yay cache..."

rm -rf "$HOME/.cache/yay/$PKGNAME" || true

echo "======================================"
echo "✅ RELEASE COMPLETE: v$VERSION"
echo "======================================"

echo ""
echo "👉 Now install/update with:"
echo "   yay -S $PKGNAME"
