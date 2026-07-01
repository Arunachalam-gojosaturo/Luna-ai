# LUNA CLI - Interactive Demonstration

## Getting Started

```bash
# Install LUNA
cd luna-cli
pip install -e ".[providers]"

# Run setup
luna setup
```

## Demo 1: Basic Chat

```bash
# Start chat
$ luna chat
You: What is Python?

LUNA: Python is a high-level, general-purpose programming language...
[streams response in real-time]
```

## Demo 2: Provider Configuration

```bash
# List available providers
$ luna api list

# Add new provider
$ luna api add
[Interactive menu to select provider and enter API key]

# Test connection
$ luna api test groq
Testing connection...
✓ Connection OK - Groq is working

# Set default
$ luna api default openai
✓ Default provider set to openai
```

## Demo 3: Git Integration

```bash
# Check git status
$ luna git status
 M luna/cli.py
 M luna/commands/chat.py
?? new_file.txt

# View changes
$ luna git diff

# Commit changes
$ luna git commit "Add new features"

# Push to remote
$ luna git push
```

## Demo 4: System Operations

```bash
# Show system info
$ luna system info
OS: Linux 7.0.12-arch1-1
Python: 3.14.6
Architecture: x86_64
Hostname: archlinux
CPU Count: 12
Home Directory: /home/arunachalam

# Run a command
$ luna system run "npm test"
[Executes command and shows output]

# Show directory tree
$ luna system tree -d 2
luna-cli
├── docs
│   └── INSTALLATION.md
├── luna
│   ├── __init__.py
│   ├── cli.py
│   ├── providers
│   └── ...
└── README.md
```

## Demo 5: Session Management

```bash
# Show recent sessions
$ luna chat history
Recent sessions:
  1. abc123 (12 messages) — groq
  2. def456 (8 messages) — openai
  3. ghi789 (15 messages) — gemini

# Continue session
$ luna chat continue abc123
[Loads previous conversation and continues]

# Export conversation
$ luna chat export abc123
[Saves as markdown file]
```

## Demo 6: Workspace Trust

```bash
# Trust current directory
$ luna trust add .
✓ Workspace Trusted
Workspace added to trusted list: /path/to/project

# List trusted workspaces
$ luna trust list
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳────────────────┓
┃ Path                      ┃ Level   ┃ Trusted At     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇────────────────┩
│ /home/arunachalam/project │ execute │ 2026-07-01...  │
└───────────────────────────┴─────────┴────────────────┘

# Check if trusted
$ luna trust check .
✓ Workspace is trusted: /home/arunachalam/project
```

## Demo 7: Configuration

```bash
# Show configuration
$ luna config
🌙 LUNA — Configuration

Current Settings:
  Workspace: /home/arunachalam/Music/luna-os
  Provider: groq
  Default Provider: groq
  Streaming: True
  Markdown: True

Configured Providers:
  • groq
  • openai
  • gemini
```

## Demo 8: Advanced Chat Features

```bash
# Chat with specific provider
$ luna chat -p openai
[Uses OpenAI instead of default]

# Load existing session
$ luna chat -s abc123
[Resumes conversation from abc123]

# Initial message
$ luna chat "Explain quantum computing"
You: Explain quantum computing

LUNA: Quantum computing represents a fundamental shift in computing...
[streams full response]
```

## Demo 9: Setup Wizard

```bash
# First time user setup
$ luna setup
🌙 LUNA CLI Setup - First-time configuration

Welcome to LUNA CLI!
This wizard will help you set up LUNA...

Step 1: Select AI Provider
  1. groq
  2. openai
  3. gemini
  4. openrouter
  5. ollama
  6. nvidia
Choose provider (1-6): 1

Step 2: Add API Key for groq
Enter your groq API key: ••••••••••••

Step 3: Select Model (optional)
Available models:
  1. mixtral-8x7b-32768
  2. gemma-7b-it
  ...
Select model: 1

Testing connection...
✓ Connection successful!

✓ Setup Complete!
You're ready to use LUNA...
```

## Workflow Example: Code Review Session

```bash
# Initialize workspace
$ luna init
✓ LUNA initialized

# Start chat
$ luna chat
You: Review this Python function for security issues

LUNA: Looking at your code...
[Analysis and suggestions]

You: How can I improve error handling?

LUNA: Here are some improvements:
[Provides specific recommendations]

# Save conversation
You: export
[Exports to file]

# View commit status
$ luna git status

# Make changes based on suggestions
$ luna git diff
$ luna git commit "Improve security per code review"
$ luna git push
```

## Workflow Example: Learning & Documentation

```bash
# Start session
$ luna chat -p gemini

You: Explain the singleton pattern in Python

LUNA: The Singleton pattern ensures only one instance of a class exists...
[Detailed explanation with examples]

You: Show me a real-world example

LUNA: Here's how Django uses it for logging:
```python
# Code example
```

You: export
[Saves as learning reference]
```

## Keyboard Shortcuts in Chat

```bash
# Multi-line input (Ctrl+D to send)
You: [multi-line editor]

# Commands in chat
/clear     - Clear chat
/history   - Show history
/export    - Export session
/exit      - Quit chat

# History navigation (arrow keys in prompt)
Up/Down    - Previous/next inputs
```

## Tips & Tricks

### 1. Combine Providers
```bash
# Start with fast provider
$ luna chat -p groq
# Then switch to more powerful
$ luna api default openai
```

### 2. Session Workflow
```bash
# Name your sessions
$ luna new
# Tag in first message: "Session: feature-x-analysis"
```

### 3. Git Integration
```bash
# Use LUNA to help with commits
$ luna git diff
$ luna chat "Generate commit message for these changes"
$ luna git commit "<paste message>"
```

### 4. Documentation
```bash
# Generate from code
$ luna chat
You: Document this function

# Export as markdown
You: export
```

## Performance Notes

- **Startup Time**: < 1 second
- **First Request**: ~2-5 seconds (provider dependent)
- **Streaming**: Real-time chunks within milliseconds
- **Session Resume**: Instant (cached locally)
- **Memory**: ~50-100 MB

## Getting Help

```bash
# Show all commands
$ luna help

# Get command help
$ luna chat --help
$ luna api --help
$ luna git --help

# Documentation
$ cat docs/INSTALLATION.md
$ cat docs/USAGE.md
```

---

**Ready to start building with LUNA?**

```bash
luna setup
```
