# 🌙 LUNA CLI - Quick Start Guide

Get started with LUNA CLI in 5 minutes.

## ⚡ Installation (Choose One)

### Option A: From Wheel (Recommended)
```bash
pip install dist/luna_cli-0.1.0-py3-none-any.whl
```

### Option B: From Source
```bash
cd luna-cli
pip install -e .
```

### Option C: Auto Installation
```bash
bash install.sh
```

## 🎯 First Steps

### 1. Verify Installation
```bash
luna-cli version
```

Expected output:
```
🌙 LUNA — Version Info
──────────────────────────────────────────────────
LUNA CLI v0.1.0
AI Coding Assistant for LUNA OS X
```

### 2. Setup API Key (5 minutes)

Get your first API key:

**Option A: Interactive Setup**
```bash
luna-cli api add
# Follow the prompts
```

**Option B: Manual Setup with Groq (Free!)

1. Sign up at https://console.groq.com
2. Create an API key
3. Run:
```bash
luna-cli api add groq
# Paste your API key when prompted
```

### 3. Start Chatting!
```bash
luna-cli chat
```

Example conversation:
```
You: How do I install Python packages?

LUNA: You can install Python packages using pip, which is...

You: Show me an example

LUNA: Here's an example:
```python
pip install requests
```

This installs the requests library...

You: /exit
```

## 💡 Common Commands

### Chat & Conversation
```bash
# Start chatting
luna-cli chat

# Start new session
luna-cli new

# Continue previous chat
luna-cli chat continue

# Show chat history
luna-cli chat history
```

### Code Assistance
```bash
# Generate code
luna-cli code generate 'HTTP server in Python'

# Explain existing code
luna-cli code explain main.py

# Refactor code
luna-cli code refactor utils.py

# Find bugs
luna-cli code debug app.py

# Generate tests
luna-cli code test calculator.py

# Generate documentation
luna-cli code doc api.py

# Code review
luna-cli code review handler.py
```

### File Operations
```bash
# Read file
luna-cli files read requirements.txt

# Create file
luna-cli files create new_file.py

# Write to file
luna-cli files write data.txt 'Hello, World!'

# Search files
luna-cli files search '*.py'

# Get file info
luna-cli files info config.json
```

### Git Integration
```bash
# Check git status
luna-cli git status

# View commits
luna-cli git log

# See changes
luna-cli git diff

# Create commit
luna-cli git commit 'Add new feature'
```

### System Commands
```bash
# Run terminal command
luna-cli system run 'npm test'

# System info
luna-cli system info

# Directory tree
luna-cli system tree
```

### Configuration
```bash
# View current config
luna-cli config

# Setup providers
luna-cli api add

# List providers
luna-cli api list

# Test provider
luna-cli api test groq

# List models
luna-cli models list
```

## 🎮 Interactive Examples

### Example 1: Generate a Python Function
```bash
$ luna-cli code generate 'function to calculate factorial'

💡 LUNA suggests:

```python
def factorial(n):
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
```

### Example 2: Explain Code
```bash
$ luna-cli code explain main.py

📝 Code Analysis:

The main.py file contains a Flask web application...
- Routes: /api/users, /api/posts
- Database: SQLite with ORM
- Authentication: JWT tokens
```

### Example 3: Fix Bugs
```bash
$ luna-cli code debug app.py

🐛 Potential Issues Found:

1. Line 42: Missing error handling in database connection
   Fix: Wrap in try-except block

2. Line 87: Race condition in file upload
   Fix: Use file locking mechanism
```

## ⚙️ Configuration

### Change Default Provider
```bash
# Edit ~/.config/luna/config.json
# Change: "default_provider": "groq" to "default_provider": "openai"
```

### Enable/Disable Features
```json
{
    "default_provider": "groq",
    "streaming": true,
    "markdown": true,
    "max_history": 20
}
```

## 🆘 Troubleshooting

### Command not found
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### API Key Issues
```bash
# Check if configured
luna-cli api list

# Re-add key
luna-cli api add groq

# Test connection
luna-cli api test groq
```

### ModuleNotFoundError
```bash
# Reinstall
pip install --force-reinstall /path/to/wheel
```

## 📊 Keyboard Shortcuts (In Chat)

```
Ctrl+D or /exit    - Exit chat
Tab                - Auto-complete
Up/Down            - History navigation
Ctrl+L             - Clear screen
Ctrl+R             - Search history
```

## 🌐 Supported AI Providers

| Provider | Free | Speed | Quality |
|----------|------|-------|---------|
| **Groq** | ✅ Yes | ⚡⚡⚡ | ⭐⭐⭐ |
| OpenAI | 💰 Trial | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| Gemini | ✅ Free tier | ⚡⚡ | ⭐⭐⭐⭐ |
| OpenRouter | ✅ Free | ⚡ | ⭐⭐⭐ |
| Ollama | ✅ Local | ⚡⚡ | ⭐⭐⭐ |
| NVIDIA NIM | ✅ Free | ⚡⚡ | ⭐⭐⭐⭐ |

**Recommendation**: Start with **Groq** (free, fast, reliable)

## 📚 More Resources

- Full documentation: See README.md
- Installation guide: See INSTALLATION_GUIDE.md
- GitHub: https://github.com/Arunachalam-gojosaturo/Luna-eco-system
- Issues & Support: https://github.com/Arunachalam-gojosaturo/Luna-eco-system/issues

## 💬 Need Help?

```bash
# View command help
luna-cli --help
luna-cli chat --help
luna-cli code --help

# View detailed help
luna-cli help

# Check logs
tail -f ~/.local/share/luna/logs/*.log
```

## 🚀 Next Steps

1. ✅ Install LUNA CLI
2. ✅ Add API key
3. ✅ Start chatting
4. 📖 Read full documentation
5. 🤝 Contribute to project
6. ⭐ Star on GitHub

---

**Ready?** Run: `luna-cli chat`

**Any issues?** Open an issue on GitHub!
