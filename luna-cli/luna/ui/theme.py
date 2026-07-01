"""
LUNA CLI UI theme and components.
"""

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from typing import Optional


# LUNA color theme
LUNA_THEME = Theme({
    "info": "bold cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "muted": "dim white",
    "primary": "bold blue",
    "secondary": "bold magenta",
    "accent": "bold cyan",
})

console = Console(theme=LUNA_THEME)


def print_header(title: str, subtitle: Optional[str] = None):
    """Print LUNA header."""
    header_text = Text("🌙 LUNA", style="bold cyan") + Text(" — ", style="dim") + Text(title, style="white")
    if subtitle:
        header_text += Text(" • ", style="dim") + Text(subtitle, style="dim cyan")
    console.print(header_text)
    console.print("─" * 50, style="dim cyan")


def print_status(message: str, status: str = "info"):
    """Print status message."""
    styles = {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "wait": "blue",
    }
    style = styles.get(status, "cyan")
    console.print(f"[{style}]●[/] {message}")


def print_section(title: str):
    """Print section title."""
    console.print(f"\n[bold cyan]{title}[/]")
    console.print("─" * len(title), style="dim cyan")


def print_code(code: str, language: str = "python"):
    """Print syntax-highlighted code."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def create_table(title: Optional[str] = None) -> Table:
    """Create styled table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    return table


def print_welcome():
    """Print welcome message."""
    welcome = """
[bold cyan]🌙 LUNA CLI[/] — AI Coding Assistant
[dim]Modern AI development tool inspired by Claude Code, Codex, & Copilot[/]

[bold]💬 Start Interactive Chat:[/]
  [bold green]luna-cli chat start[/]    ← Interactive chat box (like Copilot CLI)
  [cyan]luna chat new[/]           New chat session
  [cyan]luna chat history[/]       View previous chats

[bold]📝 Code Assistance:[/]
  [cyan]luna code generate[/]      Generate code
  [cyan]luna code explain[/]       Explain code
  [cyan]luna code refactor[/]      Refactor code

[bold]⚙️ Configuration:[/]
  [cyan]luna api add[/]             Configure AI providers
  [cyan]luna config[/]             View settings
  [cyan]luna help[/]               Show all commands

[bold]📚 Learn More:[/]
  [cyan]https://github.com/Arunachalam-gojosaturo/Luna-eco-system[/]
"""
    console.print(Panel(welcome, border_style="cyan", padding=(1, 2)))


def print_error(title: str, message: str):
    """Print error message."""
    console.print(Panel(
        f"[red]{message}[/]",
        title=f"[red]✗ {title}[/]",
        border_style="red",
    ))


def print_success(title: str, message: str):
    """Print success message."""
    console.print(Panel(
        f"[green]{message}[/]",
        title=f"[green]✓ {title}[/]",
        border_style="green",
    ))
