"""
Main CLI application using Typer.
Handles all command routing and execution.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional
from pathlib import Path

from luna.ui.theme import print_header, print_welcome, print_status

# Import command modules
from luna.commands import chat, api
from luna.commands.git import git_app
from luna.commands.system import system_app
from luna.commands.trust import trust_app
from luna.commands.files import files_app
from luna.commands.code import code_app
from luna.commands.models import models_app

app = typer.Typer(
    help="🌙 LUNA - AI Coding Assistant CLI for LUNA OS X",
    rich_markup_mode="rich",
    no_args_is_help=False,
    invoke_without_command=True,
)

console = Console()

# Add command groups
app.add_typer(chat.chat_app, name="chat", help="AI chat and conversations")
app.add_typer(api.api_app, name="api", help="Configure AI providers")
app.add_typer(git_app, name="git", help="Git operations")
app.add_typer(system_app, name="system", help="System and terminal operations")
app.add_typer(trust_app, name="trust", help="Manage trusted workspaces")
app.add_typer(files_app, name="files", help="File operations")
app.add_typer(code_app, name="code", help="Coding assistance")
app.add_typer(models_app, name="models", help="Manage AI models")


@app.callback()
def main_callback(ctx: typer.Context):
    """Main entry point."""
    if ctx.invoked_subcommand is None:
        # Start chat by default
        from luna.commands.chat import start
        start()


@app.command(name="setup")
def run_setup():
    """Run interactive setup wizard."""
    from luna.commands.setup import setup_wizard
    setup_wizard()


@app.command()
def version():
    """Show LUNA version."""
    from luna import __version__
    print_header("Version Info")
    console.print(f"[bold cyan]LUNA CLI[/] v{__version__}")
    console.print("[dim]AI Coding Assistant for LUNA OS X[/]")


@app.command()
def new():
    """Start new chat session."""
    from luna.commands.chat import start
    start()


@app.command(name="config")
def show_config():
    """Show current configuration."""
    print_header("Configuration")
    
    from luna.config import get_config
    from luna.core.session import get_session_manager
    
    config = get_config()
    session = get_session_manager()
    
    console.print("\n[bold cyan]Current Settings:[/]")
    console.print(f"  Workspace: {session.get_workspace()}")
    console.print(f"  Provider: {session.get_provider()}")
    console.print(f"  Default Provider: {config.config.default_provider}")
    console.print(f"  Streaming: {config.config.streaming}")
    console.print(f"  Markdown: {config.config.markdown}")
    
    console.print("\n[bold cyan]Configured Providers:[/]")
    if config.providers:
        for name in config.providers:
            console.print(f"  • {name}")
    else:
        console.print("  [yellow]None configured - run 'luna api add'[/]")


@app.command(name="help")
def show_help():
    """Show detailed help."""
    help_text = """
[bold cyan]🌙 LUNA CLI - Commands Reference[/]

[bold]Chat & Conversation:[/]
  [cyan]luna chat[/]               Start interactive chat
  [cyan]luna new[/]                Start new chat session  
  [cyan]luna chat history[/]       Show recent sessions
  [cyan]luna chat continue ID[/]   Resume session

[bold]Configuration:[/]
  [cyan]luna api add[/]             Add AI provider
  [cyan]luna api list[/]            List configured providers
  [cyan]luna api test PROVIDER[/]   Test provider connection
  [cyan]luna api default[/]         Set default provider
  [cyan]luna config[/]              Show current settings

[bold]Git Integration:[/]
  [cyan]luna git status[/]          Show git status
  [cyan]luna git log[/]             Show commit history
  [cyan]luna git diff[/]            Show changes
  [cyan]luna git commit[/]          Create commit

[bold]System Operations:[/]
  [cyan]luna system run[/]          Run terminal command
  [cyan]luna system info[/]         Show system info
  [cyan]luna system tree[/]         Show directory tree

[bold]Security:[/]
  [cyan]luna trust add[/]           Trust workspace
  [cyan]luna trust list[/]          List trusted workspaces
  [cyan]luna trust check[/]         Check if trusted

[bold]General:[/]
  [cyan]luna version[/]             Show version
  [cyan]luna help[/]                Show this help
  [cyan]luna init[/]                Initialize workspace

[bold]Examples:[/]
  [cyan]luna chat[/]                              Start chatting
  [cyan]luna chat -p groq[/]                      Chat with Groq
  [cyan]luna api add[/]                          Setup new provider
  [cyan]luna git status[/]                       Check git status
  [cyan]luna system run 'npm test'[/]            Run command

[bold]Coding Assistance:[/]
  [cyan]luna code explain FILE[/]                 Explain code
  [cyan]luna code generate DESC[/]                Generate code
  [cyan]luna code refactor FILE[/]                Refactor code
  [cyan]luna code debug FILE[/]                   Find bugs
  [cyan]luna code test FILE[/]                    Generate tests
  [cyan]luna code doc FILE[/]                     Generate docs
  [cyan]luna code review FILE[/]                  Review code

[bold]File Operations:[/]
  [cyan]luna files read FILE[/]                   Read file
  [cyan]luna files write FILE[/]                  Write file
  [cyan]luna files create FILE[/]                 Create file
  [cyan]luna files delete FILE[/]                 Delete file
  [cyan]luna files search PATTERN[/]              Search files
  [cyan]luna files info FILE[/]                   Get file info

[bold]Model Management:[/]
  [cyan]luna models list[/]                       Show available models
  [cyan]luna models info MODEL[/]                 Model details
"""
    console.print(Panel(help_text, title="LUNA Commands", border_style="cyan", expand=False))


@app.command(name="init")
def initialize():
    """Initialize LUNA in current directory."""
    print_header("Initialize LUNA")
    
    from luna.core.session import get_session_manager
    import os
    
    workspace = os.getcwd()
    session = get_session_manager()
    session.set_workspace(workspace)
    
    console.print(f"\n[green]✓[/] LUNA initialized in: {workspace}")
    print_status("Configuration ready", "success")


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
