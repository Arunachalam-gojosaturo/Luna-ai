"""
System integration command.
Handle terminal commands and system operations.
"""

import typer
from rich.console import Console
from rich.panel import Panel
import subprocess
import shlex
from typing import Optional

console = Console()

system_app = typer.Typer(help="System and terminal operations")


@system_app.command(name="run")
def run_command(
    command: str = typer.Argument(help="Command to run"),
    shell: bool = typer.Option(False, "--shell", "-s", help="Run with shell"),
):
    """Run a system command."""
    from luna.ui.theme import print_header, print_status
    
    print_header("Running Command", command[:50])
    
    try:
        if shell:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        else:
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        
        if result.stdout:
            console.print(result.stdout)
        
        if result.returncode == 0:
            print_status("Command completed successfully", "success")
        else:
            if result.stderr:
                console.print(f"[red]{result.stderr}[/]")
            print_status(f"Command failed (exit code: {result.returncode})", "error")
    
    except subprocess.TimeoutExpired:
        print_status("Command timeout", "error")
    except Exception as e:
        print_status(f"Error: {str(e)}", "error")


@system_app.command(name="info")
def system_info():
    """Show system information."""
    from luna.ui.theme import print_header
    import platform
    import os
    
    print_header("System Information")
    
    info_lines = [
        f"OS: {platform.system()} {platform.release()}",
        f"Python: {platform.python_version()}",
        f"Architecture: {platform.machine()}",
        f"Hostname: {platform.node()}",
        f"CPU Count: {os.cpu_count()}",
        f"Home Directory: {os.path.expanduser('~')}",
    ]
    
    console.print("\n".join(info_lines))


@system_app.command(name="env")
def show_env(
    filter: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter environment variables"),
):
    """Show environment variables."""
    from luna.ui.theme import print_header
    import os
    
    print_header("Environment Variables")
    
    env_vars = dict(os.environ)
    
    if filter:
        env_vars = {k: v for k, v in env_vars.items() if filter.lower() in k.lower()}
    
    for key, value in sorted(env_vars.items())[:20]:
        # Hide sensitive values
        if any(s in key.upper() for s in ["PASSWORD", "TOKEN", "SECRET", "KEY"]):
            value = "***"
        console.print(f"[cyan]{key}[/] = {value}")


@system_app.command(name="which")
def which_command(command: str = typer.Argument(help="Command to find")):
    """Find command in PATH."""
    from luna.ui.theme import print_status
    
    result = subprocess.run(["which", command], capture_output=True, text=True)
    
    if result.returncode == 0:
        print_status(f"Found: {result.stdout.strip()}", "success")
    else:
        print_status(f"Command not found: {command}", "warning")


@system_app.command(name="tree")
def show_tree(
    path: str = typer.Argument(".", help="Directory to show"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum depth"),
    ignore: Optional[str] = typer.Option(None, "--ignore", "-i", help="Ignore patterns"),
):
    """Show directory tree."""
    from luna.ui.theme import print_header
    from pathlib import Path
    
    print_header("Directory Tree", path)
    
    def tree(directory, prefix="", current_depth=0):
        if current_depth >= depth:
            return
        
        try:
            entries = sorted(Path(directory).iterdir())
        except PermissionError:
            return
        
        # Filter entries
        if ignore:
            entries = [e for e in entries if ignore not in e.name]
        
        entries = [e for e in entries if not e.name.startswith(".")]
        
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            current = "└── " if is_last else "├── "
            console.print(f"{prefix}{current}{entry.name}")
            
            if entry.is_dir() and current_depth < depth - 1:
                extension = "    " if is_last else "│   "
                tree(entry, prefix + extension, current_depth + 1)
    
    tree(path)


@system_app.command(name="disk")
def disk_usage(path: str = typer.Argument(".", help="Path to check")):
    """Show disk usage."""
    from luna.ui.theme import print_header
    import shutil
    
    print_header("Disk Usage", path)
    
    try:
        usage = shutil.disk_usage(path)
        total = usage.total / (1024**3)  # GB
        used = usage.used / (1024**3)
        free = usage.free / (1024**3)
        
        percent = (used / total) * 100 if total > 0 else 0
        
        console.print(f"Total: {total:.2f} GB")
        console.print(f"Used:  {used:.2f} GB ({percent:.1f}%)")
        console.print(f"Free:  {free:.2f} GB")
    except Exception as e:
        from luna.ui.theme import print_status
        print_status(f"Error: {str(e)}", "error")


def main():
    """Main entry point."""
    system_app()


if __name__ == "__main__":
    system_app()
