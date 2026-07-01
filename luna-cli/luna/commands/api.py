"""
API configuration command.
Interactive provider setup with API key management.
"""

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from typing import Optional
import subprocess

from luna.config import get_config
from luna.ui.theme import print_header, print_status, print_section, print_success, print_error
from luna.providers import ProviderRegistry

console = Console()

api_app = typer.Typer(help="Configure AI providers and API keys")


@api_app.command(name="add")
def add_provider(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider name"),
):
    """Add or update API provider."""
    print_header("Add Provider", "Configure a new AI provider")
    
    config = get_config()
    available = ProviderRegistry.list_providers()
    
    if not provider:
        console.print("\n[cyan]Available providers:[/]")
        for i, p in enumerate(available, 1):
            console.print(f"  {i}. {p}")
        
        choice = Prompt.ask("Select provider", choices=available)
        provider = choice
    
    if provider not in available:
        print_error("Invalid Provider", f"Provider '{provider}' not found")
        return
    
    # Get API key
    api_key = Prompt.ask(f"Enter {provider} API key", password=True)
    
    # Optional: get model preference
    try:
        provider_class = ProviderRegistry.get(provider)
        if provider_class:
            models = provider_class("").get_available_models()
            if models:
                console.print(f"\n[cyan]Available models for {provider}:[/]")
                for i, model in enumerate(models[:5], 1):
                    console.print(f"  {i}. {model}")
                
                model = Prompt.ask("Select model (or press Enter to skip)", default="")
            else:
                model = None
    except Exception:
        model = None
    
    # Save provider
    config.add_provider(provider, api_key, model=model)
    
    # Test connection
    console.print("\n[cyan]Testing connection...[/]")
    try:
        import asyncio
        provider_class = ProviderRegistry.get(provider)
        if provider_class:
            provider_instance = provider_class(api_key, model=model)
            result = asyncio.run(provider_instance.test_connection())
            if result:
                print_status(f"Connection successful!", "success")
                print_success("Provider Added", f"{provider} configured and tested successfully")
            else:
                print_status("Connection test failed", "warning")
                print_error("Test Failed", "Could not verify connection. Check your API key.")
    except Exception as e:
        print_error("Connection Error", str(e))


@api_app.command(name="test")
def test_provider(provider: str = typer.Argument(help="Provider to test")):
    """Test API connection for a provider."""
    print_header("Test Provider", f"Testing {provider} connection")
    
    config = get_config()
    provider_cfg = config.get_provider(provider)
    
    if not provider_cfg or not provider_cfg.api_key:
        print_error("Not Configured", f"Provider '{provider}' not configured")
        return
    
    console.print(f"\n[cyan]Testing {provider}...[/]")
    
    try:
        import asyncio
        provider_class = ProviderRegistry.get(provider)
        if provider_class:
            instance = provider_class(provider_cfg.api_key, model=provider_cfg.model)
            result = asyncio.run(instance.test_connection())
            
            if result:
                print_success("Connection OK", f"{provider} connection is working")
            else:
                print_error("Connection Failed", f"Could not reach {provider} API")
    except Exception as e:
        print_error("Error", str(e))


@api_app.command(name="list")
def list_providers():
    """List configured providers."""
    print_header("Configured Providers")
    
    config = get_config()
    
    if not config.providers:
        console.print("[yellow]No providers configured[/]")
        console.print("Run [cyan]luna /api add[/] to add a provider")
        return
    
    console.print(f"\n[cyan]Configured providers:[/]")
    for name, cfg in config.providers.items():
        has_key = "✓" if cfg.api_key else "✗"
        model_str = f" ({cfg.model})" if cfg.model else ""
        status = "[green]configured[/]" if cfg.api_key else "[red]missing key[/]"
        console.print(f"  [{has_key}] {name}{model_str} — {status}")
    
    default = config.config.default_provider
    console.print(f"\n[cyan]Default provider:[/] {default}")


@api_app.command(name="default")
def set_default(provider: str = typer.Argument(help="Provider to set as default")):
    """Set default provider."""
    config = get_config()
    config.set_default_provider(provider)
    print_success("Default Provider", f"Default provider set to {provider}")


@api_app.command(name="remove")
def remove_provider(provider: str = typer.Argument(help="Provider to remove")):
    """Remove provider configuration."""
    config = get_config()
    
    if provider not in config.providers:
        print_error("Not Found", f"Provider '{provider}' not configured")
        return
    
    if Confirm.ask(f"Remove {provider}?"):
        del config.providers[provider]
        config.save_providers()
        print_success("Removed", f"{provider} configuration removed")


def main(ctx: typer.Context):
    """Main API command entry point."""
    if ctx.invoked_subcommand is None:
        # Show interactive menu
        print_header("API Configuration")
        console.print("[cyan]What would you like to do?[/]")
        console.print("  1. Add/update provider")
        console.print("  2. List providers")
        console.print("  3. Test connection")
        console.print("  4. Set default provider")
        console.print("  5. Remove provider")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            add_provider()
        elif choice == "2":
            list_providers()
        elif choice == "3":
            provider = Prompt.ask("Enter provider name")
            test_provider(provider)
        elif choice == "4":
            provider = Prompt.ask("Enter provider name")
            set_default(provider)
        elif choice == "5":
            provider = Prompt.ask("Enter provider name")
            remove_provider(provider)


if __name__ == "__main__":
    api_app()
