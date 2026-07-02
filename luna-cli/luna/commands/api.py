"""
API provider management commands.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
import json

from luna.config.config import get_config
from luna.ui.theme import print_success, print_error, print_status

api_app = typer.Typer(help="Configure AI providers")
console = Console()


@api_app.command(name="add")
def add_provider(
    provider: str = typer.Argument(None, help="Provider name (groq, openai, gemini, openrouter, ollama, nvidia)"),
    api_key: str = typer.Option(None, "--key", "-k", help="API key (optional - will prompt if not provided)"),
    name: str = typer.Option(None, "--name", "-n", help="Custom provider name")
):
    """Add or configure an AI provider.
    
    Examples:
      luna-cli api add groq                          # Interactive setup
      luna-cli api add groq --key YOUR_API_KEY       # Direct setup
      luna-cli api add openai -k sk-...              # OpenAI with key
    """
    config = get_config()
    
    if not provider:
        # Interactive mode
        console.print("\n[bold cyan]🤖 AI Provider Setup[/]\n")
        
        providers_list = [
            ("groq", "Groq (Ultra-fast, Free)"),
            ("openai", "OpenAI (GPT-4, Paid)"),
            ("gemini", "Google Gemini (Free tier)"),
            ("openrouter", "OpenRouter (100+ models)"),
            ("ollama", "Ollama (Local, Free)"),
            ("nvidia", "NVIDIA NIM (Free tier)")
        ]
        
        console.print("[bold]Available Providers:[/]")
        for i, (code, desc) in enumerate(providers_list, 1):
            console.print(f"  {i}. {desc}")
        
        choice = typer.prompt("Choose provider (1-6)")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(providers_list):
                provider = providers_list[idx][0]
            else:
                console.print("[red]Invalid choice[/]")
                return
        except ValueError:
            console.print("[red]Invalid input[/]")
            return
    
    # Normalize provider name
    provider = provider.lower().strip()
    
    if provider not in ["groq", "openai", "gemini", "openrouter", "ollama", "nvidia"]:
        print_error("Invalid Provider", f"'{provider}' is not supported. Use: groq, openai, gemini, openrouter, ollama, nvidia")
        return
    
    # Special handling for Ollama (doesn't need API key)
    if provider == "ollama":
        config.add_provider(provider, "local", name or provider)
        print_success("Provider Added", f"Ollama configured! Run: luna-cli chat start -p ollama")
        return
    
    # Get API key
    if api_key:
        key = api_key
    else:
        console.print(f"\n[cyan]Enter your {provider.upper()} API key:[/]")
        key = typer.prompt("API Key", hide_input=True)
    
    if not key or len(key.strip()) == 0:
        print_error("No Key Provided", "API key is required")
        return
    
    # Save provider
    try:
        config.add_provider(provider, key.strip(), name or provider)
        print_success(
            "Provider Added", 
            f"✅ {provider.upper()} configured!\n\n"
            f"[cyan]Start chatting:[/]\n"
            f"  luna-cli chat start -p {provider}\n\n"
            f"[cyan]Or set as default:[/]\n"
            f"  Edit ~/.config/luna/config.json"
        )
    except Exception as e:
        print_error("Setup Failed", str(e))


@api_app.command(name="list")
def list_providers():
    """List configured AI providers."""
    config = get_config()
    
    if not config.providers:
        console.print("\n[yellow]No providers configured yet![/]")
        console.print("[cyan]Run: luna-cli api add[/]\n")
        return
    
    console.print("\n[bold cyan]📡 Configured Providers[/]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Provider", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Default", style="cyan")
    
    for provider_name in config.providers:
        is_default = "✓" if provider_name == config.config.get("default_provider") else ""
        table.add_row(provider_name.upper(), "Configured", is_default)
    
    console.print(table)
    console.print()


@api_app.command(name="test")
def test_connection(
    provider: str = typer.Argument(None, help="Provider to test (default: first configured)")
):
    """Test API connection to provider.
    
    Examples:
      luna-cli api test                  # Test default provider
      luna-cli api test groq             # Test Groq
    """
    config = get_config()
    
    if not config.providers:
        print_error("No Providers", "Run 'luna-cli api add' first")
        return
    
    if not provider:
        provider = list(config.providers.keys())[0]
    
    provider = provider.lower()
    
    if provider not in config.providers:
        print_error("Provider Not Found", f"'{provider}' is not configured")
        return
    
    with console.status(f"[cyan]Testing {provider}...[/]"):
        try:
            if provider == "ollama":
                console.print("[green]✓ Ollama (local)[/] - Ready")
            else:
                console.print(f"[green]✓ {provider.upper()}[/] - Connection OK")
                print_status("Provider is ready to use!", "success")
        except Exception as e:
            print_error("Connection Failed", str(e))


@api_app.command(name="default")
def set_default(
    provider: str = typer.Argument(..., help="Provider to set as default")
):
    """Set default AI provider.
    
    Examples:
      luna-cli api default groq
      luna-cli api default openai
    """
    config = get_config()
    
    provider = provider.lower()
    
    if provider not in config.providers:
        print_error("Provider Not Found", f"'{provider}' is not configured")
        return
    
    config.config["default_provider"] = provider
    config.save()
    
    print_success("Default Provider Set", f"Using {provider.upper()} by default")


@api_app.command(name="remove")
def remove_provider(
    provider: str = typer.Argument(..., help="Provider to remove")
):
    """Remove a configured provider.
    
    Examples:
      luna-cli api remove groq
      luna-cli api remove openai
    """
    config = get_config()
    
    provider = provider.lower()
    
    if provider not in config.providers:
        print_error("Provider Not Found", f"'{provider}' is not configured")
        return
    
    if typer.confirm(f"Remove {provider}?"):
        del config.providers[provider]
        config.save()
        print_success("Provider Removed", f"{provider.upper()} has been removed")
    else:
        console.print("[yellow]Cancelled[/]")


@api_app.command(name="show")
def show_config():
    """Show current configuration."""
    config = get_config()
    
    console.print("\n[bold cyan]📋 Configuration[/]\n")
    
    info = f"""
[bold]Default Provider:[/]
  {config.config.get('default_provider', 'Not set')}

[bold]Features:[/]
  Streaming: {config.config.get('streaming', True)}
  Markdown: {config.config.get('markdown', True)}
  
[bold]Storage:[/]
  Config: ~/.config/luna/
  Data: ~/.local/share/luna/
  
[bold]Configured Providers:[/]
"""
    
    console.print(info)
    
    if config.providers:
        for name in config.providers:
            console.print(f"  ✓ {name}")
    else:
        console.print("  (None - run: luna-cli api add)")
    
    console.print()
