# LUNA CLI Installation Guide

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Optional: Git (for git integration)

## Installation Methods

### Method 1: From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/Arunachalam-gojosaturo/luna-cli.git
cd luna-cli

# Install in development mode
pip install -e .

# Install with all AI providers
pip install -e ".[providers]"
```

### Method 2: Using pip

```bash
# Install from GitHub
pip install git+https://github.com/Arunachalam-gojosaturo/luna-cli.git

# Install with providers
pip install git+https://github.com/Arunachalam-gojosaturo/luna-cli.git[providers]
```

### Method 3: Using pipx (Recommended for Users)

```bash
# Install globally with pipx
pipx install git+https://github.com/Arunachalam-gojosaturo/luna-cli.git

# Install with providers
pipx install git+https://github.com/Arunachalam-gojosaturo/luna-cli.git[providers]
```

## Platform-Specific Instructions

### Linux / macOS

```bash
# Install Python 3.10+
# Ubuntu/Debian:
sudo apt-get install python3.10 python3.10-venv python3-pip

# macOS (using Homebrew):
brew install python@3.10

# Install LUNA
pip install -e ".[providers]"
```

### Windows

```bash
# Install Python 3.10+ from python.org
# Or use Windows Package Manager:
winget install Python.Python.3.10

# Install LUNA
pip install -e ".[providers]"
```

### Arch Linux

```bash
# Install dependencies
sudo pacman -S python python-pip

# Install LUNA
pip install --break-system-packages -e ".[providers]"

# Or use pipx
pacman -S python-pipx
pipx install git+https://github.com/Arunachalam-gojosaturo/luna-cli.git[providers]
```

## Verifying Installation

```bash
# Check installation
luna --version

# Show help
luna help

# Run setup wizard
luna setup
```

## Dependencies

### Core Dependencies

- `typer[all]>=0.9.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `httpx>=0.24.0` - HTTP client
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variables
- `platformdirs>=3.10.0` - Config/data directories

### Provider Dependencies (Optional)

- `groq>=0.4.0` - Groq provider
- `openai>=1.0.0` - OpenAI provider
- `google-generativeai>=0.3.0` - Gemini provider
- `openrouter>=0.1.0` - OpenRouter provider

### Optional Dependencies

- `GitPython>=3.1.0` - Git integration
- `websockets>=11.0` - WebSocket support
- `textual>=0.30.0` - Advanced TUI

## Configuration

### First-Time Setup

After installation, run the setup wizard:

```bash
luna setup
```

This will guide you through:
1. Selecting an AI provider
2. Adding your API key
3. Choosing a model
4. Setting your workspace

### Manual Configuration

```bash
# Add API provider manually
luna api add

# List configured providers
luna api list

# Test provider connection
luna api test groq

# Set default provider
luna api default groq
```

### Environment Variables

Create a `.env` file in your project root:

```bash
# ~/.env or /path/to/project/.env
GROQ_API_KEY=your_api_key_here
OPENAI_API_KEY=sk-your_key_here
GEMINI_API_KEY=your_key_here
```

## API Keys

### Getting API Keys

#### Groq
1. Visit https://console.groq.com
2. Sign up or log in
3. Create API key
4. Save key securely

#### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Create API key
3. Store key safely

#### Google Gemini
1. Visit https://ai.google.dev
2. Get API key
3. Use in LUNA

#### OpenRouter
1. Visit https://openrouter.ai
2. Create account and key
3. Configure in LUNA

#### Ollama (Local)
1. Install Ollama from https://ollama.ai
2. Run `ollama serve`
3. Configure LUNA to use local URL

#### NVIDIA NIM
1. Get API key from NVIDIA
2. Obtain function ID
3. Configure in LUNA

## Updating LUNA

```bash
# Update from source
cd luna-cli
git pull origin main
pip install -e ".[providers]" --upgrade

# Update via pip
pip install --upgrade luna-cli[providers]
```

## Uninstalling

```bash
# Using pip
pip uninstall luna-cli

# Using pipx
pipx uninstall luna-cli
```

## Troubleshooting

### Command Not Found

```bash
# Verify installation
pip show luna-cli

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### Import Errors

```bash
# Reinstall with dependencies
pip install -e ".[providers]" --force-reinstall

# Check Python version
python --version
```

### Provider Connection Issues

```bash
# Test provider
luna api test groq

# Check API key
echo $GROQ_API_KEY

# Verify network
luna system info
```

### Permission Denied

```bash
# Linux/macOS
chmod +x ~/.local/bin/luna

# Use pipx instead
pipx install git+https://github.com/Arunachalam-gojosaturo/luna-cli.git[providers]
```

## Development Setup

For contributing to LUNA:

```bash
# Clone repository
git clone https://github.com/Arunachalam-gojosaturo/luna-cli.git
cd luna-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[providers,dev]"

# Run tests
pytest

# Run linter
ruff check luna/

# Format code
black luna/
```

## Docker Support (Coming Soon)

```bash
# Build Docker image
docker build -t luna-cli .

# Run in Docker
docker run -it luna-cli setup
```

## Next Steps

After installation:

1. **Run setup wizard**
   ```bash
   luna setup
   ```

2. **Start chatting**
   ```bash
   luna chat
   ```

3. **Explore commands**
   ```bash
   luna help
   ```

4. **Read documentation**
   ```bash
   luna help
   cat docs/USAGE.md
   ```

## Support

- **Issues**: https://github.com/Arunachalam-gojosaturo/luna-cli/issues
- **Discussions**: https://github.com/Arunachalam-gojosaturo/luna-cli/discussions
- **Documentation**: See `docs/` folder

## License

MIT - See LICENSE file for details
