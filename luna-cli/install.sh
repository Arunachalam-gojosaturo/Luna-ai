#!/bin/bash
# LUNA CLI Installation Script for Arch Linux
# This script packages and installs LUNA CLI globally on your system

set -e

echo "🌙 LUNA CLI - Installation Script"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on Arch Linux
if ! grep -q "Arch\|Manjaro" /etc/os-release 2>/dev/null; then
    echo -e "${YELLOW}⚠️  This script is optimized for Arch Linux${NC}"
    echo "Continuing with generic Linux installation..."
fi

# Step 1: Build the package
echo -e "${BLUE}📦 Building LUNA CLI package...${NC}"
cd "$(dirname "$0")"

# Remove old build artifacts
rm -rf build/ dist/ *.egg-info/

# Build wheel
python -m pip install --upgrade build setuptools wheel > /dev/null 2>&1
python -m build > /dev/null 2>&1

echo -e "${GREEN}✓ Package built successfully${NC}"
echo ""

# Step 2: Install the package
echo -e "${BLUE}🔧 Installing LUNA CLI globally...${NC}"

# Find the wheel file
WHEEL_FILE=$(ls -t dist/*.whl 2>/dev/null | head -1)

if [ -z "$WHEEL_FILE" ]; then
    echo -e "${RED}❌ Error: Wheel file not found${NC}"
    exit 1
fi

echo "Installing: $WHEEL_FILE"

# Install with pip (with break-system-packages if needed)
if python -m pip install "$WHEEL_FILE" --break-system-packages > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Installation successful${NC}"
else
    # Fallback without break-system-packages
    python -m pip install "$WHEEL_FILE" > /dev/null 2>&1
fi

echo ""

# Step 3: Verify installation
echo -e "${BLUE}✓ Verifying installation...${NC}"

if command -v luna-cli &> /dev/null; then
    echo -e "${GREEN}✓ luna-cli command is available${NC}"
else
    echo -e "${YELLOW}⚠️  luna-cli command not found in PATH${NC}"
    echo "Adding ~/.local/bin to PATH in your shell profile..."
    
    # Add to shell profiles if not already there
    for profile in ~/.bashrc ~/.zshrc ~/.bash_profile ~/.profile; do
        if [ -f "$profile" ]; then
            if ! grep -q ".local/bin" "$profile" 2>/dev/null; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
                echo "Added to $profile"
            fi
        fi
    done
    
    echo ""
    echo "Please run: source ~/.bashrc (or ~/.zshrc for zsh)"
    echo "Then restart your terminal"
fi

echo ""

# Step 4: Show version
echo -e "${BLUE}📋 LUNA CLI Version:${NC}"
luna-cli version || python -m luna.cli version

echo ""

# Step 5: Show next steps
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Setup API key: ${YELLOW}luna-cli api add${NC}"
echo "  2. Start chatting: ${YELLOW}luna-cli chat${NC}"
echo "  3. See help:      ${YELLOW}luna-cli help${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo "  ${YELLOW}luna-cli chat${NC}              # Start interactive chat"
echo "  ${YELLOW}luna-cli code generate 'factorial function'${NC}"
echo "  ${YELLOW}luna-cli files read main.py${NC}"
echo "  ${YELLOW}luna-cli git status${NC}"
echo ""
echo "Documentation: https://github.com/Arunachalam-gojosaturo/Luna-eco-system"
echo ""
