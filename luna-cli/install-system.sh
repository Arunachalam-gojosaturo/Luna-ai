#!/bin/bash
# LUNA CLI - System-wide Installation
# This script performs a complete system-wide installation
# Run this as a regular user (not sudo)

set -e

echo "🌙 LUNA CLI - System-wide Installation"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -q "Arch\|Manjaro" /etc/os-release; then
            echo "arch"
        elif grep -q "Ubuntu\|Debian" /etc/os-release; then
            echo "debian"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEEL_FILE="$SCRIPT_DIR/dist/luna_cli-0.1.0-py3-none-any.whl"

echo -e "${CYAN}Detected OS: $OS${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Step 1: Build wheel if not exists
if [ ! -f "$WHEEL_FILE" ]; then
    echo -e "${BLUE}📦 Building wheel package...${NC}"
    cd "$SCRIPT_DIR"
    
    # Install build tools
    python3 -m pip install --user build setuptools wheel > /dev/null 2>&1
    
    # Build
    rm -rf build/ dist/ *.egg-info/
    python3 -m build > /dev/null 2>&1
    echo -e "${GREEN}✓ Wheel built${NC}"
else
    echo -e "${GREEN}✓ Wheel already exists${NC}"
fi

echo ""

# Step 2: Install wheel
echo -e "${BLUE}🔧 Installing LUNA CLI...${NC}"

if [ "$OS" = "arch" ]; then
    python3 -m pip install --user "$WHEEL_FILE" --break-system-packages > /dev/null 2>&1 || \
    python3 -m pip install --user "$WHEEL_FILE" > /dev/null 2>&1
else
    python3 -m pip install --user "$WHEEL_FILE" > /dev/null 2>&1
fi

echo -e "${GREEN}✓ Installation complete${NC}"
echo ""

# Step 3: Add to PATH
echo -e "${BLUE}🔐 Configuring PATH...${NC}"

USER_BIN="$HOME/.local/bin"
SHELLS=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile")

PATH_ADDED=false
for shell_rc in "${SHELLS[@]}"; do
    if [ -f "$shell_rc" ]; then
        if ! grep -q ".local/bin" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "# LUNA CLI" >> "$shell_rc"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$shell_rc"
            echo -e "${GREEN}✓ Added to $shell_rc${NC}"
            PATH_ADDED=true
        fi
    fi
done

if [ "$PATH_ADDED" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Please run: ${CYAN}source ~/.bashrc${YELLOW} (or ~/.zshrc for zsh)${NC}"
fi

echo ""

# Step 4: Verify installation
echo -e "${BLUE}✓ Verifying installation...${NC}"

# Add to current PATH for verification
export PATH="$USER_BIN:$PATH"

if command -v luna-cli &> /dev/null; then
    echo -e "${GREEN}✓ luna-cli command available${NC}"
else
    echo -e "${YELLOW}⚠️  luna-cli not in current PATH${NC}"
    echo "It will be available after you restart your terminal"
fi

echo ""

# Step 5: Show version and info
echo -e "${CYAN}Version Information:${NC}"
if command -v luna-cli &> /dev/null; then
    luna-cli version 2>/dev/null || python3 -m luna.cli version 2>/dev/null
fi

echo ""

# Step 6: Configuration
echo -e "${BLUE}📝 Configuration Directory:${NC}"
CONFIG_DIR="$HOME/.config/luna"
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    echo -e "${GREEN}✓ Created $CONFIG_DIR${NC}"
else
    echo -e "${GREEN}✓ Already exists: $CONFIG_DIR${NC}"
fi

echo ""
echo -e "${BLUE}📂 Data Directory:${NC}"
DATA_DIR="$HOME/.local/share/luna"
if [ ! -d "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR/logs"
    mkdir -p "$DATA_DIR/sessions"
    echo -e "${GREEN}✓ Created $DATA_DIR${NC}"
else
    echo -e "${GREEN}✓ Already exists: $DATA_DIR${NC}"
fi

echo ""

# Step 7: Success message
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Installation Complete!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Step 8: Next steps
echo -e "${CYAN}📋 Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Restart your terminal${NC} or run:"
echo "   ${CYAN}source ~/.bashrc${NC}"
echo ""
echo "2. ${YELLOW}Setup your first AI provider${NC}:"
echo "   ${CYAN}luna-cli api add${NC}"
echo ""
echo "3. ${YELLOW}Start chatting${NC}:"
echo "   ${CYAN}luna-cli chat${NC}"
echo ""

# Step 9: Useful commands
echo -e "${CYAN}📚 Useful Commands:${NC}"
echo ""
echo "  ${YELLOW}luna-cli --help${NC}         Show all commands"
echo "  ${YELLOW}luna-cli help${NC}           Detailed help"
echo "  ${YELLOW}luna-cli version${NC}        Show version"
echo "  ${YELLOW}luna-cli config${NC}         Show configuration"
echo "  ${YELLOW}luna-cli api list${NC}       List configured providers"
echo ""

# Step 10: Support
echo -e "${CYAN}💬 Need Help?${NC}"
echo ""
echo "  GitHub: https://github.com/Arunachalam-gojosaturo/Luna-eco-system"
echo "  Issues: https://github.com/Arunachalam-gojosaturo/Luna-eco-system/issues"
echo ""

echo -e "${YELLOW}🚀 Ready to start? Type: ${CYAN}luna-cli chat${NC}"
echo ""
