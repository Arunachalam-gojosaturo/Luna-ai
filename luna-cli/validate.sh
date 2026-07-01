#!/bin/bash
# LUNA CLI - Comprehensive Validation Test Suite
# Tests all features and verifies installation

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
test_command() {
    local name="$1"
    local command="$2"
    local expected_pattern="${3:-.}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -ne "${BLUE}Testing: ${name}...${NC} "
    
    if output=$(eval "$command" 2>&1); then
        if echo "$output" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}✓ PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (Pattern not found)"
            echo "  Expected pattern: $expected_pattern"
            echo "  Output: $output" | head -3
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Command failed)"
        echo "  Error: $output" | head -3
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Header
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   LUNA CLI - Validation Test Suite v0.1.0  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Command Availability
echo -e "${YELLOW}[1] Testing Command Availability${NC}"
echo "────────────────────────────────"
test_command "luna-cli command exists" "which luna-cli" "luna-cli"
test_command "luna command exists" "which luna" "luna"
echo ""

# Test 2: Help System
echo -e "${YELLOW}[2] Testing Help System${NC}"
echo "────────────────────────────────"
test_command "Default help" "luna-cli --help" "Commands"
test_command "Detailed help" "luna-cli help" "LUNA CLI"
test_command "Command help - chat" "luna-cli chat --help" "Commands"
test_command "Command help - api" "luna-cli api --help" "Commands"
test_command "Command help - code" "luna-cli code --help" "Commands"
test_command "Command help - files" "luna-cli files --help" "Commands"
test_command "Command help - git" "luna-cli git --help" "Commands"
test_command "Command help - system" "luna-cli system --help" "Commands"
test_command "Command help - models" "luna-cli models --help" "Commands"
echo ""

# Test 3: Version Information
echo -e "${YELLOW}[3] Testing Version Information${NC}"
echo "────────────────────────────────"
test_command "Version command" "luna-cli version" "v0.1.0"
echo ""

# Test 4: Configuration
echo -e "${YELLOW}[4] Testing Configuration${NC}"
echo "────────────────────────────────"
test_command "Config display" "luna-cli config" "Settings"
test_command "API list" "luna-cli api list" "Provider"
echo ""

# Test 5: Subcommand Availability
echo -e "${YELLOW}[5] Testing Subcommands${NC}"
echo "────────────────────────────────"

# Chat subcommands
test_command "Chat history subcommand" "luna-cli chat history --help" "Show"

# Code subcommands
test_command "Code explain" "luna-cli code explain --help" "Explain"
test_command "Code generate" "luna-cli code generate --help" "Generate"
test_command "Code refactor" "luna-cli code refactor --help" "Refactor"
test_command "Code debug" "luna-cli code debug --help" "Debug"
test_command "Code test" "luna-cli code test --help" "Test"
test_command "Code doc" "luna-cli code doc --help" "Doc"
test_command "Code review" "luna-cli code review --help" "Review"

# File subcommands
test_command "Files read" "luna-cli files read --help" "Read"
test_command "Files write" "luna-cli files write --help" "Write"
test_command "Files create" "luna-cli files create --help" "Create"
test_command "Files delete" "luna-cli files delete --help" "Delete"
test_command "Files search" "luna-cli files search --help" "Search"
test_command "Files info" "luna-cli files info --help" "Info"

# Git subcommands
test_command "Git status" "luna-cli git status --help" "Status"
test_command "Git log" "luna-cli git log --help" "Log"
test_command "Git diff" "luna-cli git diff --help" "Diff"

# System subcommands
test_command "System run" "luna-cli system run --help" "Run"
test_command "System info" "luna-cli system info --help" "Info"
test_command "System tree" "luna-cli system tree --help" "Tree"

# Models commands
test_command "Models list" "luna-cli models list --help" "List"
test_command "Models info" "luna-cli models info --help" "Info"

echo ""

# Test 6: Configuration Files
echo -e "${YELLOW}[6] Testing Configuration Directories${NC}"
echo "────────────────────────────────"

CONFIG_DIR="$HOME/.config/luna"
DATA_DIR="$HOME/.local/share/luna"

if [ -d "$CONFIG_DIR" ]; then
    echo -e "${GREEN}✓${NC} Config directory exists: $CONFIG_DIR"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Config directory missing: $CONFIG_DIR"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

if [ -d "$DATA_DIR" ]; then
    echo -e "${GREEN}✓${NC} Data directory exists: $DATA_DIR"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Data directory missing: $DATA_DIR"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo ""

# Test 7: Global Accessibility
echo -e "${YELLOW}[7] Testing Global Accessibility${NC}"
echo "────────────────────────────────"

# Test from different directory
if cd /tmp && luna-cli version > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Command works from /tmp"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Command doesn't work from /tmp"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

if cd / && luna-cli version > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Command works from /"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Command doesn't work from /"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo ""

# Test 8: Documentation Files
echo -e "${YELLOW}[8] Testing Documentation${NC}"
echo "────────────────────────────────"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS=(
    "README.md"
    "INSTALLATION_GUIDE.md"
    "QUICK_START.md"
    "PROJECT_STATUS.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$SCRIPT_DIR/$doc" ]; then
        echo -e "${GREEN}✓${NC} Found: $doc"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Missing: $doc"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
done

echo ""

# Test 9: Installation Files
echo -e "${YELLOW}[9] Testing Installation Files${NC}"
echo "────────────────────────────────"

FILES=(
    "pyproject.toml"
    "install.sh"
    "install-system.sh"
    "PKGBUILD"
)

for file in "${FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "${GREEN}✓${NC} Found: $file"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Missing: $file"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
done

echo ""

# Test 10: Python Modules
echo -e "${YELLOW}[10] Testing Python Modules${NC}"
echo "────────────────────────────────"

test_command "Import luna module" "python3 -c 'import luna'" ""
test_command "Import luna.cli" "python3 -c 'from luna import cli'" ""
test_command "Import luna.chat" "python3 -c 'from luna.chat import chat'" ""
test_command "Import luna.providers" "python3 -c 'from luna.providers import base'" ""

echo ""

# Summary
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          Test Summary                      ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

PASS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))

echo -e "Total Tests:    ${CYAN}$TESTS_TOTAL${NC}"
echo -e "Tests Passed:   ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed:   ${RED}$TESTS_FAILED${NC}"
echo -e "Pass Rate:      ${CYAN}${PASS_RATE}%${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! LUNA CLI is ready for production use.${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Add API provider: ${YELLOW}luna-cli api add${NC}"
    echo "  2. Start chatting:   ${YELLOW}luna-cli chat${NC}"
    echo "  3. View help:        ${YELLOW}luna-cli help${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
