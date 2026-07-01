# 🌙 LUNA CLI - Installation Guide

Complete installation instructions for LUNA CLI v0.1.0 on various platforms.

## 📋 Requirements

- **Python**: 3.10 or higher
- **OS**: Linux (Arch, Ubuntu, Debian), macOS, Windows (WSL)
- **RAM**: 512 MB minimum
- **Disk**: 200 MB for full installation

## 🚀 Installation Methods

### Method 1: Arch Linux (Native Package)

Currently available for manual installation. Full AUR package coming soon.

```bash
# Clone the repository
git clone https://github.com/Arunachalam-gojosaturo/Luna-eco-system.git
cd Luna-eco-system/luna-cli

# Build and install
bash install.sh
```

### Method 2: PIP (Universal)

**Recommended for all platforms**

```bash
# Install directly from wheel
pip install dist/luna_cli-0.1.0-py3-none-any.whl

# Or install in editable mode for development
pip install -e .

# Add ~/.local/bin to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### Method 3: Virtual Environment (Recommended for Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install LUNA CLI
pip install -e .

# Test
luna-cli version
```

### Method 4: Pipx (Isolated Environment)

```bash
# Install pipx if not installed
pacman -S python-pipx  # Arch Linux

# Install LUNA CLI
pipx install /path/to/luna_cli-0.1.0-py3-none-any.whl

# Verify
luna-cli --help
```

## ✅ Verification

After installation, verify everything works:

```bash
# Check version
luna-cli version

# Check help
luna-cli help

# List all commands
luna-cli --help

# Test a specific command
luna-cli config
```

## 🔑 Initial Setup

### 1. Add AI Provider (Required)

```bash
# Interactive setup wizard
luna-cli api add

# Or add specific provider
luna-cli api add groq
# Enter your Groq API key when prompted
```

**Get API Keys:**
- **Groq**: https://console.groq.com
- **OpenAI**: https://platform.openai.com/api-keys
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **OpenRouter**: https://openrouter.ai
- **NVIDIA NIM**: https://build.nvidia.com

### 2. Initialize Workspace

```bash
# Initialize LUNA in your project directory
cd /path/to/your/project
luna-cli init
```

### 3. Start Chatting

```bash
luna-cli chat
```

## 📦 What Gets Installed

```
~/.local/bin/
├── luna              # Main command
└── luna-cli          # Alias command

~/.config/luna/
├── config.json       # Configuration
└── providers.json    # API keys (secure)

~/.local/share/luna/
├── logs/             # Application logs
└── sessions/         # Chat history
```

## 🔒 Security Notes

- API keys stored locally in `~/.config/luna/`
- No data sent to external servers except AI providers
- Each provider has encrypted credential storage
- Trust system prevents accidental file modifications

## 🐛 Troubleshooting

### Command not found after installation

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Add to shell profile
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### ModuleNotFoundError

```bash
# Reinstall with dependencies
pip install --force-reinstall /path/to/wheel

# Or install with dependencies
pip install -e . --break-system-packages
```

### API Connection Issues

```bash
# Test API connection
luna-cli api test groq

# Check configuration
luna-cli config

# View logs
tail -f ~/.local/share/luna/logs/*.log
```

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.10+

# Use specific Python version
python3.11 -m luna.cli chat
```

## 📚 Quick Start Guide

```bash
# 1. Start interactive chat
luna-cli chat

# 2. Generate code
luna-cli code generate 'fibonacci function'

# 3. Explain code
luna-cli code explain main.py

# 4. Check git status
luna-cli git status

# 5. Read file
luna-cli files read requirements.txt

# 6. List available models
luna-cli models list

# 7. Run system command
luna-cli system run 'npm test'
```

## 🛠️ Development Installation

```bash
# Clone repository
git clone https://github.com/Arunachalam-gojosaturo/Luna-eco-system.git
cd Luna-eco-system/luna-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black luna/

# Type checking
mypy luna/
```

## 📝 Configuration

Edit `~/.config/luna/config.json`:

```json
{
    "default_provider": "groq",
    "streaming": true,
    "markdown": true,
    "max_history": 20,
    "workspace": "/current/path"
}
```

## 🗑️ Uninstallation

```bash
# Remove via pip
pip uninstall luna-cli

# Remove configuration and data
rm -rf ~/.config/luna
rm -rf ~/.local/share/luna

# Remove from shell profile if manually added
# Edit ~/.bashrc, ~/.zshrc, etc. to remove PATH export
```

## 💬 Support & Contributing

- **Issues**: https://github.com/Arunachalam-gojosaturo/Luna-eco-system/issues
- **Discussions**: https://github.com/Arunachalam-gojosaturo/Luna-eco-system/discussions
- **Contributing**: See CONTRIBUTING.md in repository

## 📄 License

LUNA CLI is licensed under the MIT License. See LICENSE file for details.

---

**Version**: 0.1.0 Beta  
**Last Updated**: July 1, 2024  
**Maintained by**: Arunachalam
