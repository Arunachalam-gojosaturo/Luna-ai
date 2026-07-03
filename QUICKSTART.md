# 🌙 Luna OS v2 - Quick Start Guide

**Status**: ✅ Installation Complete  
**Installation Location**: `~/.local/opt/luna-os`  
**Latest Build**: July 4, 2026

---

## 🚀 Launch Your Application

### Option 1: Terminal
```bash
luna-os
```

### Option 2: Application Menu
Search for **"Luna OS v2"** in your application launcher (Activities/applications)

### Option 3: Direct Binary
```bash
~/.local/opt/luna-os/src-tauri/target/release/app
```

---

## ⏱️ First Run

1. **Application starts** → Window opens
2. **Backend initializes** → Takes 3-5 seconds (first time longer due to Python startup)
3. **React UI loads** → Beautiful interface appears
4. **System connects** → Backend communicates with frontend
5. **Ready to use** → Interact with your AI assistant

---

## 📁 Important File Locations

### Application Data
```
~/.local/opt/luna-os/              # Main installation

~/.local/share/luna-os/            # Databases & cache
  ├── luna_chat.db                 # Chat history
  └── luna_chroma_db/              # Vector memory

~/.config/luna-os/                 # Configuration files

~/.cache/luna-os/logs/             # Application logs
```

### Troubleshooting
- **Check logs**: `tail -f ~/.cache/luna-os/logs/*.log`
- **Reinstall backend**: `cd ~/.local/opt/luna-os && source venv/bin/activate && pip install -r requirements.txt`
- **Reset data**: `rm -rf ~/.local/share/luna-os/* ~/.config/luna-os/*`

---

## ✨ Features Included

### 🧠 AI Brain
- Multiple LLM providers (Gemini, Groq, OpenAI, OpenRouter)
- Intelligent decision engine
- Real-time response generation
- Context awareness

### 🗣️ Voice Interaction
- Speech-to-Text (STT)
- Text-to-Speech (TTS) with configurable voices
- Real-time voice commands
- Audio streaming

### 🗄️ Memory System
- Long-term semantic memory (ChromaDB)
- Chat history (SQLite)
- Context preservation across sessions
- Automatic memory management

### 🐧 Linux Integration
- Execute system commands
- Package management (pacman)
- File operations
- Git integration
- System monitoring

### 💻 Developer Workspace
- Git repository integration
- Code assistance
- Project management
- File browsing

### 📊 System Dashboard
- Real-time system metrics
- CPU/RAM/Disk monitoring
- Process monitoring
- Network status

---

## 🔧 Configuration

### Settings Panel
Launch the app and access Settings to configure:
- Speech recognition settings
- TTS voice and speed
- API keys for LLM providers
- Visual themes
- Microphone input
- Output device

### API Keys Setup
Required keys to add in Settings:
1. **Gemini API Key** - Get from https://ai.google.dev
2. **Groq API Key** (optional) - Get from https://console.groq.com
3. **OpenAI API Key** (optional) - Get from https://platform.openai.com
4. **OpenRouter API Key** (optional) - Get from https://openrouter.ai

---

## 🎯 Common Tasks

### Interact with AI
1. Click the microphone icon to record voice
2. Or type text in the input field
3. Wait for AI response
4. Listen to audio response (if enabled)

### Use Developer Workspace
1. Navigate to Developer tab
2. Connect a Git repository
3. Browse files and get AI assistance
4. View system metrics

### Check Memory/History
1. Go to Memory section
2. See all past interactions
3. Search previous conversations
4. View semantic memory

### Configure Voice
1. Open Settings
2. Go to Voice/TTS section
3. Select voice
4. Adjust speed and pitch
5. Test audio

---

## 📝 CLI Usage

Luna OS also includes a command-line interface:

```bash
# Run enhanced CLI
npm run cli

# Check configuration
npm run cli:config

# Run CLI tests
npm run cli:test
```

CLI Features:
- `help` - Show all commands
- `status` - System statistics
- `history` - Recent interactions
- `clear` - Clear screen
- `model` - Switch AI model
- `voice` - Voice settings
- `memory` - Memory operations
- `exit` - Quit CLI

---

## 🐛 Troubleshooting

### App Won't Start
```bash
# Check if backend starts manually
cd ~/.local/opt/luna-os
source venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 3000
```

### Backend Connection Failed
```bash
# Verify backend is running
lsof -i :3000

# Check logs
tail -f ~/.cache/luna-os/logs/*
```

### Audio/Microphone Issues
```bash
# Reinstall audio packages
sudo pacman -S portaudio
cd ~/.local/opt/luna-os
source venv/bin/activate
pip install pyaudio
```

### Memory Issues
```bash
# Reset databases
rm ~/.local/share/luna-os/luna_chat.db
rm -rf ~/.local/share/luna-os/luna_chroma_db/

# App will recreate on next run
```

### Permission Denied
```bash
# Fix ownership
chown -R $USER:$USER ~/.local/opt/luna-os
chmod -R u+rwx ~/.local/opt/luna-os
```

---

## 📊 System Requirements

### Minimum
- CPU: 2 cores @ 2.0 GHz
- RAM: 4 GB
- Storage: 1 GB
- OS: Arch Linux (or compatible)

### Recommended
- CPU: 4+ cores @ 2.5 GHz
- RAM: 8+ GB
- Storage: 2 GB SSD
- GPU: Optional (for faster AI responses)

### Required Packages
All automatically installed via `install.sh`:
- `python` (3.10+)
- `nodejs` (18+)
- `rustc` (1.70+)
- `portaudio` (audio)
- `base-devel` (build tools)

---

## 🔄 Uninstall

To completely remove Luna OS:

```bash
# Remove application
rm -rf ~/.local/opt/luna-os

# Remove launcher
rm ~/.local/bin/luna-os

# Remove desktop file
rm ~/.local/share/applications/luna-os.desktop

# Remove icon
rm ~/.local/share/icons/hicolor/128x128/apps/luna-os.png

# Remove user data
rm -rf ~/.local/share/luna-os
rm -rf ~/.config/luna-os
rm -rf ~/.cache/luna-os
```

---

## 🆘 Getting Help

### Check Logs
```bash
ls -lh ~/.cache/luna-os/logs/
tail -f ~/.cache/luna-os/logs/*.log
```

### Verify Installation
```bash
which luna-os
cat ~/.local/share/applications/luna-os.desktop
ls -lh ~/.local/opt/luna-os/src-tauri/target/release/app
```

### Test Components
```bash
# Test Python
python3 --version

# Test Node
node --version

# Test Python packages
source ~/.local/opt/luna-os/venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"
```

---

## 📚 Documentation

- **Full Installation Report**: `INSTALLATION_REPORT.md`
- **Bug Fixes Report**: `BUG_FIXES_REPORT.md`
- **CLI Guide**: `CLI_GUIDE.md`
- **Project README**: `README.md`

---

## ✅ What's Fixed

### Major Fixes Applied
1. ✅ **Backend Auto-Startup** - Tauri now spawns Python backend
2. ✅ **Path Resolution** - XDG-compliant database locations
3. ✅ **Desktop Integration** - Application menu entry and icon
4. ✅ **Installation** - Proper Arch Linux installer
5. ✅ **Packaging** - Python packaging configuration
6. ✅ **14 Previous Bugs** - All critical issues resolved

### Total Improvements
- **7 New Files** created
- **3 Files** modified
- **275+ Lines** of new code
- **Production-Ready** deployment

---

## 🎉 You're All Set!

Your Luna OS v2 is ready to use. Launch it now:

```bash
luna-os
```

Enjoy your AI-powered operating system! 🚀

---

**Last Updated**: July 4, 2026  
**Version**: 2.0.0  
**Status**: Production Ready ✅

For more information, visit: https://github.com/Arunachalam-gojosaturo/Luna-eco-system
