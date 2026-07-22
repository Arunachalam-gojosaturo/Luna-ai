# 🌙 Luna CLI - Enhanced Command Line Interface

## Overview

Luna CLI is an advanced, feature-rich command line interface for Luna OS X. It provides a modern, interactive way to communicate with the Luna AI assistant with awesome boot animations, attribute-based commands, and rich terminal UI.

## Quick Start

### Installation

The enhanced CLI is ready to use. Make sure your Python virtual environment is activated:

```bash
# Make sure backend is running
npm run start

# In a new terminal, run the enhanced CLI
npm run cli
```

Or directly:

```bash
python luna_cli_enhanced.py
```

## Features

### 🎨 Rich Terminal UI

- **Colorized Output**: Beautiful ANSI color coding for all output
- **ASCII Tables**: Formatted tables for displaying data
- **Progress Bars**: Visual feedback for long operations
- **Spinners**: Animated loading indicators with multiple styles
- **Boxes & Sections**: Decorative elements for better readability

### ⚡ Boot Animation

When you start the CLI, you'll see:
- Luna logo with animation
- Colorized boot sequence with loading indicators
- System initialization status
- Ready for commands message

### 🎯 Attribute-Based Commands

Commands are organized as objects with attributes:

```
CLICommand:
  - name: "help"
  - description: "Show available commands"
  - aliases: ["h", "?"]
  - category: "system"
  - status: "active"
```

### 📝 Available Commands

#### System Commands
- **help** (aliases: h, ?)
  Show all available commands organized by category

- **status** (aliases: stat)
  Display Luna system status, uptime, command statistics

- **history** (aliases: hist)
  View recent command history from current session

- **clear** (aliases: cls)
  Clear the terminal screen

- **exit** (aliases: quit, q)
  Exit the CLI gracefully

#### Configuration Commands
- **model** (aliases: m)
  Switch between AI models/providers (Groq, OpenAI, Google, OpenRouter)

- **voice** (aliases: v)
  Toggle voice output on/off

#### Memory Commands
- **memory** (aliases: mem)
  Manage Luna's memory system (list, search, clear, stats)

### 💾 Session Management

Each CLI session includes:
- Unique session ID
- Command history
- Success/failure tracking
- Uptime tracking
- Model/provider tracking

View session stats with the `status` command.

## Configuration

Luna CLI uses a configuration system stored in `~/.luna/cli/`:

### Configuration Files

```
~/.luna/cli/
├── config.json          # Global settings
├── profiles.json        # User profiles
├── aliases.json         # Custom command aliases
├── history.json         # Command history
└── cache/               # Cache directory
```

### Configuration Manager

Access configuration programmatically:

```python
from cli_config import ConfigManager, CLIProfile

# Load configuration
config = ConfigManager()

# Access current profile
print(config.current_profile.model)  # "groq"

# Create new profile
profile = config.create_profile(
    "coding",
    model="gpt-4",
    provider="openai",
    voice_enabled=False
)

# Switch profiles
config.switch_profile("coding")

# Save settings
config.save_settings()
```

### Creating Custom Profiles

```bash
# In Python
from cli_config import ConfigManager

config = ConfigManager()
profile = config.create_profile(
    "research",
    model="gpt-4",
    provider="openai",
    auto_confirm=True
)
```

## CLI Utilities

### Colors

Access ANSI color codes:

```python
from cli_utils import Colors

print(f"{Colors.BRIGHT_GREEN}Success!{Colors.RESET}")
print(f"{Colors.BRIGHT_RED}Error!{Colors.RESET}")
```

### Progress Bars

```python
from cli_utils import ProgressBar

bar = ProgressBar(100, "Processing", length=40)
for i in range(101):
    bar.update(i)
    time.sleep(0.01)
```

### Spinners

```python
from cli_utils import Spinner

spinner = Spinner("Loading", "dots")
for _ in range(30):
    spinner.start()
    time.sleep(0.1)
spinner.stop("✓ Loaded!")
```

Spinner types: `dots`, `line`, `arrow`, `box`, `moon`

### Tables

```python
from cli_utils import Table

table = Table(["Name", "Status", "Description"], [20, 15, 35])
table.add_row(["command1", "Active", "Does something"])
table.add_row(["command2", "Inactive", "Does something else"])
table.display()
```

### Messages

```python
from cli_utils import (
    print_success, print_error, print_warning, print_info,
    print_box, print_section, create_divider
)

print_success("Operation completed!")
print_error("Something went wrong!")
print_warning("Be careful!")
print_info("FYI: This is important")

print_box("Important message", title="Alert")
print_section("New Section")
```

## Custom Aliases

Add custom command shortcuts:

```python
from cli_config import CommandAliasManager

alias_mgr = CommandAliasManager()

# Add custom alias
alias_mgr.add_alias("st", "status")
alias_mgr.add_alias("sm", "system memory")

# List all aliases
aliases = alias_mgr.list_aliases()
for alias, command in aliases.items():
    print(f"{alias} -> {command}")
```

## History Management

```python
from cli_config import HistoryManager

history = HistoryManager()

# Search history
results = history.search("help")

# Get recent entries
recent = history.get_recent(10)

# Export history
history.export("history_backup.json")

# Clear history
history.clear()
```

## Advanced Features

### Session Attributes

```
CLISession:
  - session_id: Unique identifier
  - created_at: Session start time
  - user: Username
  - model: AI model in use
  - provider: AI provider
  - history: Command history
  - total_commands: Total commands executed
  - successful_commands: Successful commands
  - failed_commands: Failed commands
```

### Command Attributes

```
CLICommand:
  - name: Command name
  - description: What it does
  - aliases: Alternative names
  - requires_confirmation: Ask before executing
  - category: Command category
  - status: Current status
```

## Usage Examples

### Basic Command

```
luna> help
```

### Check Status

```
luna> status
```

### View History

```
luna> history
```

### Switch Model

```
luna> model
# Shows options to select from

luna> 1
# Switches to Groq
```

### Enable Voice

```
luna> voice
```

### Get System Memory Info

```
luna> memory
```

### Exit

```
luna> exit
```

## Environment Variables

The CLI uses these environment variables:

```bash
# API Keys for LLMs
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_API_KEY=your_google_key

# Backend URL
LUNA_API_URL=http://localhost:3000

# WebSocket URL
LUNA_WS_URL=ws://localhost:3000
```

## Running CLI Tests

Test the CLI utilities:

```bash
npm run cli:test
```

This will demonstrate:
- Progress bars
- Spinners
- Tables
- Status messages
- Boxes and sections

## Keyboard Shortcuts

- **Ctrl+C**: Exit CLI gracefully
- **Ctrl+D**: EOF, also exits
- **Tab**: Command auto-completion (when implemented)
- **Up Arrow**: Previous command (history)
- **Down Arrow**: Next command (history)

## Troubleshooting

### CLI won't connect to backend

```bash
# Make sure backend is running
npm run start

# Check if port 3000 is accessible
curl http://localhost:3000/health
```

### WebSocket connection fails

```bash
# Verify WebSocket URL
# Backend should have ws://localhost:3000/api/ws/events
```

### Colors not showing

```bash
# Some terminals don't support ANSI colors
# Colors are automatically detected and disabled if unsupported
```

## Architecture

### Components

1. **LunaCliEnhanced**: Main CLI class with command processing
2. **CLICommand**: Command object with attributes
3. **CLISession**: Session management with statistics
4. **BootAnimation**: Animated startup sequence
5. **Colors**: ANSI color definitions

### Flow

1. User starts CLI
2. Boot animation plays
3. CLI loads session configuration
4. WebSocket listener starts in background
5. Command prompt appears
6. User enters command
7. CLI processes local commands or sends to backend
8. Response displayed
9. Repeat until exit

## Contributing

To extend the CLI:

1. Add new command to `_init_commands()`
2. Create handler method like `async def handle_<command>()`
3. Add command processing in `process_local_command()`

Example:

```python
async def handle_newcommand(self) -> None:
    """Handle new command"""
    print(self._format_header("New Command"))
    print("Output here")

# Add to _init_commands
"newcommand": CLICommand(
    name="newcommand",
    description="Description",
    aliases=["nc"],
    category="category"
)

# Add to process_local_command
elif cmd_name == "newcommand":
    await self.handle_newcommand()
```

## Performance Tips

1. **Disable animations for scripts**: Set `animations_enabled=False` in settings
2. **Reduce history size**: Lower `history_size` in profile for faster startup
3. **Use profiles**: Separate profiles for different use cases
4. **Cache results**: Use built-in cache directory for repeated queries

## License

Part of Luna OS X project.

---

**Enjoy using Luna CLI! 🚀**

For more info about Luna OS X, visit: https://github.com/Arunachalam-gojosaturo/Luna-eco-system
