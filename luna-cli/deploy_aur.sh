#!/bin/bash
set -e

echo "Cleaning up temp directory..."
rm -rf /tmp/aur-luna-cli

echo "Cloning AUR repository..."
git clone ssh://aur@aur.archlinux.org/luna-cli.git /tmp/aur-luna-cli
cd /tmp/aur-luna-cli

echo "Copying local PKGBUILD..."
cp /home/arunachalam/Music/luna-os-v2/luna-cli/PKGBUILD ./PKGBUILD

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
