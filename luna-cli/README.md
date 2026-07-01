# 🌙 LUNA CLI

**Modern AI Coding Assistant for Developers**

LUNA CLI is a production-ready AI coding assistant built in Python with support for multiple AI providers, streaming responses, code analysis, and seamless terminal integration.

![Status](https://img.shields.io/badge/status-beta-yellow)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🤖 AI Chat
- **Streaming responses** with real-time output
- **Conversation history** with persistent sessions
- **Multi-line input** for complex queries
- **Session management** - resume previous chats
- **Export conversations** as markdown

### 🔧 Multi-Provider Support
- **Groq** - Fast, efficient LLMs
- **OpenAI** - GPT-4, GPT-3.5
- **Google Gemini** - Powerful generative AI
- **OpenRouter** - Access to 100+ models
- **Ollama** - Local AI models
- **NVIDIA NIM** - Enterprise AI

### 💻 System Integration
- **Git operations** - status, commits, diffs, branches
- **Terminal commands** - run shell commands naturally
- **File operations** - read, write, analyze files
- **System info** - check resources and environment
- **Directory tree** - visualize projects

### 🔐 Trust & Security
- **Trusted workspaces** - selective command execution
- **Permission levels** - granular control
- **Secure storage** - API keys in `~/.config/luna/`
- **No hardcoded secrets** - environment-safe

### 🎨 Beautiful Terminal UI
- **Rich formatting** - colors, tables, panels
- **Syntax highlighting** - code blocks with themes
- **Responsive design** - modern CLI experience
- **Progress indicators** - visual feedback

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Arunachalam-gojosaturo/luna-cli.git
cd luna-cli

# Install with providers
pip install -e ".[providers]"

# Or minimal install
pip install -e .
```

### First-Time Setup

```bash
# Run interactive setup
luna setup

# Or manual provider configuration
luna api add
```

### Start Chatting

```bash
# Basic chat
luna chat

# Chat with specific provider
luna chat -p openai

# Continue previous conversation
luna chat continue <session-id>

# Start new session explicitly
luna new
```

## 📖 Commands

### Chat & Conversation

```bash
luna chat                    # Start interactive chat
luna new                     # New chat session
luna chat history           # Show recent sessions
luna chat continue ID       # Resume session
luna chat export ID         # Export as markdown
```

### AI Provider Configuration

```bash
luna api add               # Add new provider
luna api list              # List configured providers
luna api test groq         # Test connection
luna api default openai    # Set default provider
luna api remove openai     # Remove provider
```

### Git Integration

```bash
luna git status            # Show git status
luna git log              # View commit history
luna git diff             # Show changes
luna git commit "message" # Create commit
luna git branch -c dev    # Create branch
luna git push             # Push to remote
luna git pull             # Pull from remote
```

### System Operations

```bash
luna system info          # System information
luna system run "npm test" # Execute command
luna system tree          # Directory tree
luna system env           # Environment variables
luna system disk          # Disk usage
luna system which python  # Find command
```

### Workspace Management

```bash
luna init                 # Initialize LUNA
luna config              # Show configuration
luna trust add .         # Trust current directory
luna trust list          # List trusted workspaces
luna trust check .       # Check if trusted
```

### General

```bash
luna version             # Show version
luna help               # Show help
luna setup              # Run setup wizard
```

## 🔑 Configuration

### API Keys

Store API keys securely in `~/.config/luna/`:

```bash
# Add API key interactively
luna api add

# Or set environment variable
export GROQ_API_KEY="your_key_here"
```

Supported environment variables:
- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `OLLAMA_BASE_URL`

### Config Files

```
~/.config/luna/
├── config.json              # Main configuration
├── providers.json           # Provider configs
├── trusted_workspaces.json  # Trusted paths
└── sessions.json           # Session state

~/.local/share/luna/
├── history/                # Chat history
├── logs/                   # Operation logs
└── cache/                  # Cache data
```

## 🎯 Example Workflows

### Code Analysis Chat

```bash
$ luna chat
You: Analyze this Python function for performance issues

LUNA: I'll analyze the function...
[streaming response with suggestions]
```

### Git Workflow

```bash
$ luna git status
$ luna chat
You: Help me write a commit message for these changes

$ luna git commit "Your AI-generated commit message"
$ luna git push
```

### Project Understanding

```bash
$ luna system tree -d 3
$ luna chat
You: Explain the project structure

LUNA: [explains structure based on tree]
```

## 🏗️ Architecture

### Core Components

- **`providers/`** - AI provider implementations
- **`chat/`** - Chat system with streaming
- **`commands/`** - CLI commands
- **`config/`** - Configuration management
- **`core/`** - Session & utilities
- **`ui/`** - Terminal UI components

### Data Flow

```
User Input → CLI Command → Provider Selection → 
AI Provider → Streaming Response → Terminal Display
```

### Async Architecture

- Non-blocking I/O with `asyncio`
- Concurrent API requests
- Real-time streaming responses
- Responsive terminal UI

## 🔌 Extending LUNA

### Add New Provider

```python
# luna/providers/custom.py
from luna.providers import BaseProvider

class CustomProvider(BaseProvider):
    async def chat(self, messages, **kwargs):
        # Implementation
        pass
    
    async def stream_chat(self, messages, **kwargs):
        async for chunk in response:
            yield chunk
```

### Add New Command

```python
# luna/commands/mycmd.py
import typer

mycommand_app = typer.Typer()

@mycommand_app.command()
def mycommand():
    # Implementation
    pass
```

Then register in `luna/cli.py`:

```python
app.add_typer(mycommand_app, name="mycommand")
```

## 📊 Performance

- **Startup**: < 1 second
- **API latency**: Provider-dependent
- **Memory**: ~50-100 MB idle
- **Streaming**: Real-time chunks

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=luna

# Specific provider test
pytest tests/test_providers.py::test_groq
```

## 🐛 Troubleshooting

### API Key Not Found

```bash
# Verify key is configured
luna api list

# Or set environment variable
export GROQ_API_KEY="your_key"
```

### Connection Error

```bash
# Test provider connection
luna api test groq

# Check system network
luna system info
```

### Command Execution Failed

```bash
# Trust workspace
luna trust add .

# Check permissions
luna trust list
```

## 📝 License

MIT License - see LICENSE file

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🔗 Links

- **Repository**: https://github.com/Arunachalam-gojosaturo/luna-cli
- **Issues**: https://github.com/Arunachalam-gojosaturo/luna-cli/issues
- **Documentation**: See docs/ folder

## 👨‍💻 Author

**Arunachalam** - AI Engineer & Developer

## 🙏 Acknowledgments

Inspired by:
- Claude Code
- GitHub Copilot CLI
- OpenAI Codex
- Modern AI development tools

---

**Built with ❤️ for developers by developers**

*LUNA - Making AI development accessible and productive*
