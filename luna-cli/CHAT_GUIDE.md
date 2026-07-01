# 💬 LUNA CLI - Interactive Chat Guide

**LUNA CLI has a full interactive chat interface just like Copilot CLI!**

---

## 🚀 Quick Start

### Step 1: Setup Your First AI Provider (One-time)

```bash
luna-cli api add
```

Choose one:
- **Groq** ⭐ (Free, ultra-fast) - Recommended
- **OpenAI** (Paid, best quality)
- **Gemini** (Free tier available)
- **OpenRouter** (100+ models)
- **Ollama** (Local, no API key needed)
- **NVIDIA NIM** (Free tier)

### Step 2: Start Interactive Chat

```bash
luna-cli chat start
```

This opens an **interactive chat box** where you can:
- Type messages freely
- Get streaming AI responses
- Continue conversations
- Use keyboard shortcuts

### Step 3: Chat Like Normal

```
🌙 LUNA Chat
────────────────────────────────────

You:
> What is machine learning?

LUNA:
Machine learning is a subset of artificial intelligence...

You:
> Give me Python example

LUNA:
Here's a simple example:
```python
from sklearn.tree import DecisionTreeClassifier
model = DecisionTreeClassifier()
model.fit(X_train, y_train)
```

You:
> /exit

✓ Chat saved to session
```

---

## 📝 Chat Commands

### Start Chat

```bash
# Interactive chat (this is what you want!)
luna-cli chat start

# New chat session
luna-cli chat new

# Continue previous chat
luna-cli chat continue ID

# View all previous chats
luna-cli chat history

# Export chat as markdown
luna-cli chat export ID
```

---

## ⌨️ Chat Keyboard Shortcuts

In the chat interface:

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Ctrl+D` | Exit chat |
| `Ctrl+L` | Clear screen |
| `Ctrl+R` | Search history |
| `Up/Down` | Navigate message history |
| `Tab` | Auto-complete |
| `/exit` | Exit chat |
| `/clear` | Clear chat |
| `/help` | Show help |

---

## 💡 Chat Examples

### Example 1: Ask Questions

```bash
$ luna-cli chat start

You:
> How do I read a file in Python?

LUNA:
You can use the open() function...
```

### Example 2: Get Code

```
You:
> Write a function to calculate factorial

LUNA:
```python
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
```
```

### Example 3: Debug Code

```
You:
> Why is this code slow?

LUNA:
The issue is in the nested loop...
```

### Example 4: Learn Concepts

```
You:
> Explain asyncio in Python

LUNA:
Asyncio is Python's asynchronous I/O library...
```

---

## 📊 Chat Features

✅ **Interactive Chat Box**
- Real chat interface, not command execution
- Multi-line input support
- Type freely, like any chat app

✅ **Streaming Responses**
- Responses appear in real-time
- See AI thinking as it types
- Like ChatGPT or Claude

✅ **Conversation History**
- All chats automatically saved
- Resume previous conversations
- Export as markdown

✅ **Session Persistence**
- Continue chats later
- Auto-save after each message
- Never lose a conversation

✅ **Multi-provider Support**
- Use any AI provider
- Switch providers anytime
- Fallback support

---

## 📁 Chat Data

Your chat history is stored at:

```
~/.local/share/luna/sessions/    ← Chat files
~/.local/share/luna/logs/        ← Logs
```

---

## 🔄 Using Different Providers in Chat

### Use Specific Provider

```bash
# Chat with OpenAI
luna-cli chat start -p openai

# Chat with Groq
luna-cli chat start -p groq

# Chat with Ollama (local)
luna-cli chat start -p ollama
```

### List Available Providers

```bash
luna-cli api list
```

---

## 🎯 Common Chat Tasks

### Start Coding Discussion

```bash
$ luna-cli chat start

You:
> I want to build a REST API in Python. What should I use?

LUNA:
FastAPI is a great choice...

You:
> Show me a basic example

LUNA:
Here's a simple FastAPI app...
```

### Learn a New Language

```bash
You:
> Teach me JavaScript basics

LUNA:
JavaScript is a programming language...

You:
> Show me how to use async/await

LUNA:
async/await makes asynchronous code...
```

### Debug Issues

```bash
You:
> Why am I getting this error?
> [paste error]

LUNA:
This error occurs because...

You:
> How do I fix it?

LUNA:
Here's the solution...
```

---

## ❓ FAQ

**Q: How do I know if the chat is working?**
A: Run `luna-cli chat start` - you'll see the interactive prompt. If it says provider not configured, run `luna-cli api add` first.

**Q: Can I use it without an API key?**
A: Yes! Use Ollama (local AI) or other free options.

**Q: How do I save my chat?**
A: Chats are auto-saved. Run `luna-cli chat history` to see all sessions.

**Q: Can I export my chat?**
A: Yes! Run `luna-cli chat export SESSION_ID`

**Q: How do I delete a chat?**
A: Chat files are in `~/.local/share/luna/sessions/` - delete the file or use the export feature first.

---

## 🚀 Tips & Tricks

1. **Use `/exit` to cleanly close chat** - This saves your session automatically
2. **Use Up/Down arrows** - Navigate previous messages in history
3. **Use Tab** - Auto-complete commands and providers
4. **Use Ctrl+R** - Search through your chat history
5. **Use Ctrl+L** - Clear the screen without closing chat
6. **Multi-line messages** - Type `\n` or just Enter for new lines
7. **Continue sessions** - Use `luna-cli chat continue` to resume later

---

## 🔧 Troubleshooting

### Chat Won't Start

```bash
# Check if provider is configured
luna-cli api list

# If not, add one
luna-cli api add

# Check configuration
luna-cli config
```

### No Response from AI

```bash
# Test your API connection
luna-cli api test groq  # or your provider

# Check your API key is valid
luna-cli config

# Check logs
tail -f ~/.local/share/luna/logs/*.log
```

### Chat Not Saving

```bash
# Check if directory exists
ls -la ~/.local/share/luna/sessions/

# Create if missing
mkdir -p ~/.local/share/luna/sessions/
```

---

## 📚 More Help

```bash
# See all chat commands
luna-cli chat --help

# See all commands
luna-cli help

# See API configuration help
luna-cli api --help

# See available models
luna-cli models list
```

---

## 🎉 You're Ready!

Start chatting now:

```bash
luna-cli api add      # Setup (one-time)
luna-cli chat start   # Start chatting!
```

Enjoy your AI coding assistant! 🌙

---

**Questions?** Open an issue: https://github.com/Arunachalam-gojosaturo/Luna-eco-system/issues
