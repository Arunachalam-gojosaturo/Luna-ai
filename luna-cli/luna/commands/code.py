"""
Coding assistant command.
Generate, explain, refactor, and analyze code.
"""

import typer
from rich.console import Console
from rich.syntax import Syntax
from pathlib import Path
from typing import Optional
import asyncio

console = Console()

code_app = typer.Typer(help="Coding assistance")


def get_chat_system():
    """Get configured chat system."""
    from luna.config import get_config
    from luna.providers import ProviderRegistry
    from luna.chat import ChatSystem
    
    config = get_config()
    provider_cfg = config.get_provider(config.config.default_provider)
    
    if not provider_cfg or not provider_cfg.api_key:
        console.print("[red]No AI provider configured[/]")
        raise typer.Exit(1)
    
    provider_class = ProviderRegistry.get(config.config.default_provider)
    provider = provider_class(provider_cfg.api_key, model=provider_cfg.model)
    return ChatSystem(provider)


@code_app.command(name="explain")
def explain_code(
    file: str = typer.Argument(help="File to explain"),
):
    """Explain code in a file."""
    from luna.ui.theme import print_header
    
    file_path = Path(file).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("Explain Code", str(file_path))
    
    try:
        with open(file_path) as f:
            code = f.read()
        
        chat_sys = get_chat_system()
        prompt = f"Explain this code:\n\n```\n{code}\n```\n\nProvide a clear, detailed explanation."
        
        console.print("\n[cyan]Analyzing code...[/]\n")
        
        async def stream_response():
            async for chunk in chat_sys.stream_chat(prompt):
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


@code_app.command(name="generate")
def generate_code(
    description: str = typer.Argument(help="What code to generate"),
    language: str = typer.Option("python", "--language", "-l", help="Programming language"),
    save: Optional[str] = typer.Option(None, "--save", "-s", help="Save to file"),
):
    """Generate code based on description."""
    from luna.ui.theme import print_header
    
    print_header("Generate Code", description[:50])
    
    try:
        chat_sys = get_chat_system()
        prompt = f"Generate {language} code for: {description}\n\nProvide clean, well-documented code."
        
        console.print(f"\n[cyan]Generating {language} code...[/]\n")
        
        generated = ""
        
        async def stream_response():
            nonlocal generated
            async for chunk in chat_sys.stream_chat(prompt):
                generated += chunk
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
        
        if save:
            Path(save).write_text(generated)
            console.print(f"\n[green]✓[/] Saved to {save}")
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


@code_app.command(name="refactor")
def refactor_code(
    file: str = typer.Argument(help="File to refactor"),
    focus: Optional[str] = typer.Option(None, "--focus", "-f", help="Refactoring focus"),
):
    """Suggest refactoring improvements."""
    from luna.ui.theme import print_header
    
    file_path = Path(file).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("Refactor Code", str(file_path))
    
    try:
        with open(file_path) as f:
            code = f.read()
        
        chat_sys = get_chat_system()
        focus_text = f"Focus on: {focus}. " if focus else ""
        prompt = f"{focus_text}Refactor this code for better quality:\n\n```\n{code}\n```\n\nProvide the refactored code and explain improvements."
        
        console.print("\n[cyan]Analyzing and refactoring...[/]\n")
        
        async def stream_response():
            async for chunk in chat_sys.stream_chat(prompt):
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


@code_app.command(name="debug")
def debug_code(
    file: str = typer.Argument(help="File with potential bugs"),
    issue: Optional[str] = typer.Option(None, "--issue", "-i", help="Describe the issue"),
):
    """Find and fix bugs in code."""
    from luna.ui.theme import print_header
    
    file_path = Path(file).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("Debug Code", str(file_path))
    
    try:
        with open(file_path) as f:
            code = f.read()
        
        chat_sys = get_chat_system()
        issue_text = f"Issue: {issue}. " if issue else ""
        prompt = f"{issue_text}Find and fix bugs in this code:\n\n```\n{code}\n```\n\nExplain the bugs and provide fixed code."
        
        console.print("\n[cyan]Analyzing for bugs...[/]\n")
        
        async def stream_response():
            async for chunk in chat_sys.stream_chat(prompt):
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


@code_app.command(name="test")
def generate_tests(
    file: str = typer.Argument(help="File to generate tests for"),
    framework: str = typer.Option("pytest", "--framework", "-f", help="Test framework"),
):
    """Generate unit tests for code."""
    from luna.ui.theme import print_header
    
    file_path = Path(file).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("Generate Tests", str(file_path))
    
    try:
        with open(file_path) as f:
            code = f.read()
        
        chat_sys = get_chat_system()
        prompt = f"Generate comprehensive {framework} unit tests for this code:\n\n```\n{code}\n```\n\nProvide thorough test coverage."
        
        console.print(f"\n[cyan]Generating {framework} tests...[/]\n")
        
        async def stream_response():
            async for chunk in chat_sys.stream_chat(prompt):
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


@code_app.command(name="doc")
def generate_docs(
    file: str = typer.Argument(help="File to document"),
):
    """Generate documentation for code."""
    from luna.ui.theme import print_header
    
    file_path = Path(file).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("Generate Documentation", str(file_path))
    
    try:
        with open(file_path) as f:
            code = f.read()
        
        chat_sys = get_chat_system()
        prompt = f"Generate comprehensive documentation for this code:\n\n```\n{code}\n```\n\nInclude docstrings, comments, and usage examples."
        
        console.print("\n[cyan]Generating documentation...[/]\n")
        
        async def stream_response():
            async for chunk in chat_sys.stream_chat(prompt):
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


@code_app.command(name="review")
def review_code(
    file: str = typer.Argument(help="File to review"),
    focus: Optional[str] = typer.Option(None, "--focus", "-f", help="Review focus"),
):
    """Code review and quality analysis."""
    from luna.ui.theme import print_header
    
    file_path = Path(file).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("Code Review", str(file_path))
    
    try:
        with open(file_path) as f:
            code = f.read()
        
        chat_sys = get_chat_system()
        focus_text = f"Focus on: {focus}. " if focus else ""
        prompt = f"{focus_text}Review this code for quality, security, and best practices:\n\n```\n{code}\n```\n\nProvide detailed feedback and suggestions."
        
        console.print("\n[cyan]Reviewing code...[/]\n")
        
        async def stream_response():
            async for chunk in chat_sys.stream_chat(prompt):
                console.print(chunk, end="", highlight=False)
        
        asyncio.run(stream_response())
        console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")


def main():
    """Main entry point."""
    code_app()


if __name__ == "__main__":
    code_app()
