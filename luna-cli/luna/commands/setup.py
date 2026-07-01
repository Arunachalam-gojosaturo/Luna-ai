"""
Setup wizard for LUNA CLI.
Interactive first-time setup.
"""

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from luna.ui.theme import print_header, print_success, print_status
from luna.config import get_config
from luna.providers import ProviderRegistry
from luna.core.session import get_session_manager
import os

console = Console()


def setup_wizard():
    """Run interactive setup wizard."""
    print_header("LUNA CLI Setup", "First-time configuration")
    
    console.print("""
[cyan]Welcome to LUNA CLI![/]

This wizard will help you set up LUNA for your first use.
Let's configure an AI provider to get started.
    """)
    
    # Step 1: Select provider
    console.print("[bold cyan]Step 1: Select AI Provider[/]")
    available = ProviderRegistry.list_providers()
    
    for i, provider in enumerate(available, 1):
        console.print(f"  {i}. {provider}")
    
    while True:
        choice = Prompt.ask("Choose provider (1-6)", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available):
                provider = available[idx]
                break
        except ValueError:
            pass
        console.print("[red]Invalid choice, please try again[/]")
    
    # Step 2: Get API key
    console.print(f"\n[bold cyan]Step 2: Add API Key for {provider}[/]")
    api_key = Prompt.ask(f"Enter your {provider} API key", password=True)
    
    if not api_key:
        print_status("Setup cancelled", "warning")
        return
    
    # Step 3: Get model preference
    console.print(f"\n[bold cyan]Step 3: Select Model (optional)[/]")
    try:
        provider_class = ProviderRegistry.get(provider)
        if provider_class:
            instance = provider_class("")
            models = instance.get_available_models()
            if models:
                console.print("Available models:")
                for i, model in enumerate(models[:5], 1):
                    console.print(f"  {i}. {model}")
                
                model_choice = Prompt.ask("Select model (or press Enter to skip)", default="")
                if model_choice and model_choice.isdigit():
                    idx = int(model_choice) - 1
                    if 0 <= idx < len(models):
                        model = models[idx]
                    else:
                        model = None
                else:
                    model = None
            else:
                model = None
    except Exception:
        model = None
    
    # Step 4: Save configuration
    console.print(f"\n[bold cyan]Step 4: Saving Configuration[/]")
    config = get_config()
    config.add_provider(provider, api_key, model=model)
    config.set_default_provider(provider)
    
    # Test connection
    console.print("Testing connection...")
    try:
        import asyncio
        provider_class = ProviderRegistry.get(provider)
        if provider_class:
            instance = provider_class(api_key, model=model)
            result = asyncio.run(instance.test_connection())
            if result:
                print_success(f"✓ {provider} configured successfully!", 
                            f"Ready to start chatting with {provider}")
            else:
                print_status("Connection test failed - check your API key", "warning")
    except Exception as e:
        print_status(f"Error during setup: {str(e)}", "error")
        return
    
    # Step 5: Set workspace
    console.print(f"\n[bold cyan]Step 5: Set Workspace[/]")
    workspace = Prompt.ask("Workspace directory (or press Enter for current)", default=".")
    if workspace:
        workspace = os.path.abspath(workspace)
        get_session_manager().set_workspace(workspace)
    
    console.print("""
[green bold]✓ Setup Complete![/]

You're ready to use LUNA. Try these commands:
  [cyan]luna chat[/]               Start AI chat
  [cyan]luna help[/]               Show all commands
  [cyan]luna config[/]             View configuration
    """)


if __name__ == "__main__":
    setup_wizard()
