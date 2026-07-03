#!/bin/bash
set -e

echo "Cleaning up temp directory..."
rm -rf /tmp/aur-luna-cli

echo "Cloning AUR repository..."
git clone ssh://aur@aur.archlinux.org/luna-cli.git /tmp/aur-luna-cli
cd /tmp/aur-luna-cli

echo "Generating PKGBUILD..."
cat << 'EOF' > PKGBUILD
pkgname=luna-cli
pkgver=0.1.1
pkgrel=1
pkgdesc="Your Personal AI Coding Assistant & Friend right in your Terminal."
arch=('any')
url="https://github.com/Arunachalam-gojosaturo/Luna-cli"
license=('MIT')
depends=('nodejs' 'npm')
source=("https://registry.npmjs.org/@arunachalamarc017/${pkgname}/-/${pkgname}-${pkgver}.tgz")
sha256sums=('SKIP')

package() {
  npm install -g --cache "${srcdir}/npm-cache" --prefix "${pkgdir}/usr" "${srcdir}/@arunachalamarc017/${pkgname}-${pkgver}.tgz"
  
  # Remove extra npm clutter
  rm -rf "${pkgdir}/usr/etc"
  rm -rf "${pkgdir}/usr/lib/node_modules/@arunachalamarc017/luna-cli/node_modules/puppeteer/.local-chromium" 2>/dev/null || true
}
EOF

echo "Updating checksums..."
updpkgsums

echo "Generating .SRCINFO..."
makepkg --printsrcinfo > .SRCINFO

echo "Committing to AUR..."
git add PKGBUILD .SRCINFO
git commit -m "Initial release of Luna CLI 0.1.1"

echo "Pushing to AUR..."
git push -u origin master
echo "DONE!"
