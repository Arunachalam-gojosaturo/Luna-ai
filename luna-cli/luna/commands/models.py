"""
Models command - View and manage AI models.
"""

import typer
from rich.console import Console
from rich.table import Table

console = Console()

models_app = typer.Typer(help="Manage AI models")


@models_app.command(name="list")
def list_models(provider: str = typer.Option(None, "--provider", "-p", help="Filter by provider")):
    """List available models for providers."""
    from luna.ui.theme import print_header
    from luna.providers import ProviderRegistry
    
    print_header("Available Models")
    
    if provider:
        provider_class = ProviderRegistry.get(provider)
        if not provider_class:
            console.print(f"[red]Unknown provider: {provider}[/]")
            return
        
        instance = provider_class("")
        models = instance.get_available_models()
        
        table = Table(title=f"{provider} Models", show_header=True, header_style="bold cyan")
        table.add_column("Model", style="cyan")
        
        for model in models:
            table.add_row(model)
        
        console.print(table)
    else:
        # Show all providers and their models
        for prov_name in ProviderRegistry.list_providers():
            provider_class = ProviderRegistry.get(prov_name)
            if provider_class:
                try:
                    instance = provider_class("")
                    models = instance.get_available_models()
                    
                    table = Table(title=f"{prov_name.title()} Models", show_header=True, header_style="bold cyan")
                    table.add_column("Model", style="cyan")
                    
                    for model in models[:3]:  # Show first 3
                        table.add_row(model)
                    
                    if len(models) > 3:
                        table.add_row(f"... and {len(models) - 3} more")
                    
                    console.print(table)
                    console.print()
                except Exception:
                    pass


@models_app.command(name="info")
def model_info(
    provider: str = typer.Argument(help="Provider name"),
    model: str = typer.Argument(help="Model name"),
):
    """Get information about a specific model."""
    from luna.ui.theme import print_header
    from luna.providers import ProviderRegistry
    
    provider_class = ProviderRegistry.get(provider)
    
    if not provider_class:
        console.print(f"[red]Unknown provider: {provider}[/]")
        return
    
    print_header("Model Information", f"{provider}/{model}")
    
    console.print(f"[bold cyan]Provider:[/] {provider}")
    console.print(f"[bold cyan]Model:[/] {model}")
    console.print(f"[bold cyan]Status:[/] Available")
    
    info_text = {
        "mixtral-8x7b-32768": "Groq's fast Mixtral model - 8x7B parameters, optimized for speed",
        "gemma-7b-it": "Google Gemma 7B instruction-tuned model",
        "llama-3-70b": "Meta Llama 3 70B - Large, capable model",
        "gpt-4-turbo-preview": "OpenAI GPT-4 Turbo - Most capable OpenAI model",
        "gpt-3.5-turbo": "OpenAI GPT-3.5 Turbo - Fast and efficient",
        "gemini-pro": "Google Gemini Pro - Multimodal capability",
        "mistral": "Ollama Mistral - Fast local inference",
    }
    
    description = info_text.get(model, "No additional information available")
    console.print(f"[bold cyan]Description:[/] {description}")


def main():
    """Main entry point."""
    models_app()


if __name__ == "__main__":
    models_app()
