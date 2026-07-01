"""
CLI Utilities and Helper Functions for Luna OS X
Includes formatting, progress indicators, and interactive components
"""

import sys
import time
from typing import List, Optional, Callable
from enum import Enum


class ProgressBar:
    """ASCII progress bar with customization"""
    
    def __init__(self, total: int, prefix: str = "Progress", length: int = 40):
        self.total = total
        self.prefix = prefix
        self.length = length
        self.current = 0
    
    def update(self, current: int) -> None:
        """Update progress bar"""
        self.current = current
        self.display()
    
    def increment(self) -> None:
        """Increment progress"""
        self.current += 1
        self.display()
    
    def display(self) -> None:
        """Display the progress bar"""
        percent = (self.current / self.total) * 100
        filled = int(self.length * self.current // self.total)
        bar = "█" * filled + "░" * (self.length - filled)
        
        print(f"\r{self.prefix} |{bar}| {percent:.1f}%", end="", flush=True)
        
        if self.current == self.total:
            print()


class Spinner:
    """Animated spinner for long operations"""
    
    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "arrow": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "box": ["◰", "◳", "◲", "◱"],
        "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
    }
    
    def __init__(self, message: str = "Loading", spinner_type: str = "dots"):
        self.message = message
        self.spinner_type = spinner_type
        self.index = 0
        self.running = False
        self.frames = self.SPINNERS.get(spinner_type, self.SPINNERS["dots"])
    
    def start(self) -> None:
        """Start spinner"""
        self.running = True
        self.index = 0
        self._display()
    
    def stop(self, final_message: str = "Done!") -> None:
        """Stop spinner"""
        self.running = False
        print(f"\r{final_message:<50}")
    
    def update(self, message: str = None) -> None:
        """Update spinner message and display"""
        if message:
            self.message = message
        if self.running:
            self._display()
    
    def _display(self) -> None:
        """Display current frame"""
        frame = self.frames[self.index % len(self.frames)]
        print(f"\r{frame} {self.message:<40}", end="", flush=True)
        self.index += 1
        time.sleep(0.1)


class Table:
    """ASCII table formatter"""
    
    def __init__(self, headers: List[str], widths: Optional[List[int]] = None):
        self.headers = headers
        self.rows: List[List[str]] = []
        self.widths = widths or [20] * len(headers)
    
    def add_row(self, row: List[str]) -> None:
        """Add a row to the table"""
        self.rows.append(row)
    
    def add_rows(self, rows: List[List[str]]) -> None:
        """Add multiple rows"""
        self.rows.extend(rows)
    
    def _format_row(self, row: List[str]) -> str:
        """Format a single row"""
        formatted = []
        for cell, width in zip(row, self.widths):
            formatted.append(str(cell)[:width].ljust(width))
        return "│ " + " │ ".join(formatted) + " │"
    
    def _separator(self) -> str:
        """Create table separator"""
        separators = ["─" * w for w in self.widths]
        return "├" + "┼".join(["─" * (w + 2) for w in self.widths]) + "┤"
    
    def display(self) -> None:
        """Display the table"""
        # Top border
        print("┌" + "┬".join(["─" * (w + 2) for w in self.widths]) + "┐")
        
        # Header
        print(self._format_row(self.headers))
        print(self._separator())
        
        # Rows
        for row in self.rows:
            print(self._format_row(row))
        
        # Bottom border
        print("└" + "┴".join(["─" * (w + 2) for w in self.widths]) + "┘")


class Menu:
    """Interactive menu system"""
    
    def __init__(self, title: str, items: List[tuple]):
        """
        Initialize menu
        items: List of (name, description, callback) tuples
        """
        self.title = title
        self.items = items
    
    def display(self) -> Optional[any]:
        """Display menu and return selected item"""
        print(f"\n{'─' * 50}")
        print(f"  {self.title}")
        print(f"{'─' * 50}\n")
        
        for i, (name, desc, _) in enumerate(self.items, 1):
            print(f"  {i}. {name:<20} - {desc}")
        
        print(f"\n  0. Exit")
        print()
        
        while True:
            try:
                choice = input("  Select an option: ").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                
                if 1 <= choice_num <= len(self.items):
                    name, desc, callback = self.items[choice_num - 1]
                    if callback:
                        return callback()
                    return choice_num - 1
                
                print(f"  {Colors.RED}Invalid option. Please try again.{Colors.RESET}")
            
            except ValueError:
                print(f"  {Colors.RED}Please enter a number.{Colors.RESET}")


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def print_box(text: str, color: str = Colors.BRIGHT_CYAN, title: str = "") -> None:
    """Print text in a decorative box"""
    width = len(text) + 4
    
    if title:
        print(f"{color}╔═ {title} {'═' * (width - len(title) - 4)}╗{Colors.RESET}")
    else:
        print(f"{color}╔{'═' * width}╗{Colors.RESET}")
    
    print(f"{color}║{Colors.RESET}  {text}  {color}║{Colors.RESET}")
    print(f"{color}╚{'═' * width}╝{Colors.RESET}")


def print_section(title: str, color: str = Colors.BRIGHT_CYAN) -> None:
    """Print a section header"""
    print(f"\n{color}{'─' * 60}{Colors.RESET}")
    print(f"{color}  {title.upper()}{Colors.RESET}")
    print(f"{color}{'─' * 60}{Colors.RESET}\n")


def print_success(message: str) -> None:
    """Print success message"""
    print(f"{Colors.BRIGHT_GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message"""
    print(f"{Colors.BRIGHT_RED}✗ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """Print warning message"""
    print(f"{Colors.BRIGHT_YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print info message"""
    print(f"{Colors.BRIGHT_BLUE}ℹ {message}{Colors.RESET}")


def format_command(cmd: str, category: str = "command") -> str:
    """Format a command for display"""
    icons = {
        "command": "⚡",
        "task": "📋",
        "config": "⚙️",
        "help": "❓",
        "system": "🖥️",
    }
    icon = icons.get(category, "•")
    return f"{icon} {Colors.BRIGHT_CYAN}{cmd}{Colors.RESET}"


def format_status(status: str, context: str = "") -> str:
    """Format status indicator"""
    statuses = {
        "success": (Colors.BRIGHT_GREEN, "✓"),
        "error": (Colors.BRIGHT_RED, "✗"),
        "pending": (Colors.BRIGHT_YELLOW, "⏳"),
        "running": (Colors.BRIGHT_BLUE, "⚙️"),
        "warning": (Colors.BRIGHT_YELLOW, "⚠"),
    }
    
    color, symbol = statuses.get(status, (Colors.RESET, "•"))
    result = f"{color}{symbol} {status.upper()}{Colors.RESET}"
    
    if context:
        result += f" {Colors.DIM}({context}){Colors.RESET}"
    
    return result


def clear_screen() -> None:
    """Clear terminal screen"""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')


def pause(message: str = "Press Enter to continue...") -> None:
    """Pause and wait for user input"""
    input(f"\n{Colors.DIM}{message}{Colors.RESET}")


def create_divider(length: int = 60, char: str = "─", color: str = Colors.DIM) -> str:
    """Create a colored divider"""
    return f"{color}{char * length}{Colors.RESET}"


if __name__ == "__main__":
    # Demo
    print("\n" + "="*60)
    print("CLI Utils Demo")
    print("="*60 + "\n")
    
    # Progress bar
    print_section("Progress Bar")
    bar = ProgressBar(100, "Processing")
    for i in range(101):
        bar.update(i)
        time.sleep(0.01)
    
    # Spinner
    print_section("Spinner")
    spinner = Spinner("Loading resources", "moon")
    for _ in range(20):
        spinner.start()
        time.sleep(0.1)
    spinner.stop("✓ Loaded!")
    
    # Table
    print_section("Table Example")
    table = Table(["Command", "Description", "Status"], [20, 35, 15])
    table.add_rows([
        ["help", "Show available commands", "Active"],
        ["voice", "Toggle voice output", "Inactive"],
        ["memory", "Manage Luna's memory", "Active"],
    ])
    table.display()
    
    # Messages
    print_section("Message Types")
    print_success("Operation completed successfully")
    print_warning("This is a warning message")
    print_error("An error occurred")
    print_info("This is informational")
    
    # Box
    print_section("Decorative Box")
    print_box("Luna CLI is ready!", Colors.BRIGHT_MAGENTA, "Welcome")
    
    print()
