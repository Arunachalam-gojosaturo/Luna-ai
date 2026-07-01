"""
File operations command.
Read, write, edit, and analyze files.
"""

import typer
from rich.console import Console
from rich.syntax import Syntax
from pathlib import Path
from typing import Optional
import os

console = Console()

files_app = typer.Typer(help="File operations")


@files_app.command(name="read")
def read_file(
    path: str = typer.Argument(help="File path to read"),
    lines: Optional[int] = typer.Option(None, "--lines", "-l", help="Number of lines"),
    syntax: str = typer.Option("text", "--syntax", "-s", help="Syntax highlighting language"),
):
    """Read and display file contents."""
    from luna.ui.theme import print_header, print_error, print_status
    
    file_path = Path(path).resolve()
    
    if not file_path.exists():
        print_error("Not Found", f"File not found: {path}")
        return
    
    if not file_path.is_file():
        print_error("Invalid", f"Not a file: {path}")
        return
    
    print_header("Read File", str(file_path))
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Limit lines if specified
        if lines:
            content = '\n'.join(content.split('\n')[:lines])
        
        # Syntax highlight
        try:
            syntax_obj = Syntax(content, syntax, theme="monokai", line_numbers=True)
            console.print(syntax_obj)
        except:
            console.print(content)
    
    except Exception as e:
        print_error("Error", str(e))


@files_app.command(name="write")
def write_file(
    path: str = typer.Argument(help="File path to write"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Content to write"),
    append: bool = typer.Option(False, "--append", "-a", help="Append instead of overwrite"),
):
    """Write content to file."""
    from luna.ui.theme import print_header, print_success, print_error
    
    file_path = Path(path).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if content is None:
            content = console.input("Enter content (Ctrl+D to finish):\n")
        
        mode = 'a' if append else 'w'
        with open(file_path, mode) as f:
            f.write(content)
        
        print_success("File Written", f"Successfully written to {file_path}")
    
    except Exception as e:
        print_error("Error", str(e))


@files_app.command(name="delete")
def delete_file(path: str = typer.Argument(help="File path to delete")):
    """Delete a file."""
    from luna.ui.theme import print_success, print_error
    from rich.prompt import Confirm
    
    file_path = Path(path).resolve()
    
    if not file_path.exists():
        print_error("Not Found", f"File not found: {path}")
        return
    
    if Confirm.ask(f"Delete {file_path}?"):
        try:
            file_path.unlink()
            print_success("Deleted", f"File deleted: {file_path}")
        except Exception as e:
            print_error("Error", str(e))


@files_app.command(name="create")
def create_file(
    path: str = typer.Argument(help="File path to create"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Template type"),
):
    """Create a new file from template."""
    from luna.ui.theme import print_success, print_error
    
    file_path = Path(path).resolve()
    
    if file_path.exists():
        print_error("Already Exists", f"File already exists: {path}")
        return
    
    templates = {
        "python": "#!/usr/bin/env python3\n\"\"\"\n{}\n\"\"\"\n\n\ndef main():\n    pass\n\nif __name__ == \"__main__\":\n    main()\n",
        "bash": "#!/bin/bash\n# {}\n\nset -euo pipefail\n\necho \"Script started\"\n",
        "markdown": "# {}\n\n## Description\n\n## Usage\n\n## Examples\n",
    }
    
    content = templates.get(template, "")
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w') as f:
            f.write(content.format(file_path.stem))
        print_success("Created", f"File created: {file_path}")
    except Exception as e:
        print_error("Error", str(e))


@files_app.command(name="search")
def search_files(
    pattern: str = typer.Argument(help="Search pattern"),
    directory: str = typer.Option(".", "--dir", "-d", help="Directory to search"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Recursive search"),
):
    """Search for files matching pattern."""
    from luna.ui.theme import print_header
    
    print_header("Search Files", pattern)
    
    search_dir = Path(directory).resolve()
    
    if recursive:
        pattern_obj = search_dir.glob(f"**/*{pattern}*")
    else:
        pattern_obj = search_dir.glob(f"*{pattern}*")
    
    matches = list(pattern_obj)
    
    if matches:
        for match in sorted(matches):
            file_type = "[DIR]" if match.is_dir() else "[FILE]"
            console.print(f"{file_type} {match}")
    else:
        console.print("[yellow]No matches found[/]")


@files_app.command(name="info")
def file_info(path: str = typer.Argument(help="File path")):
    """Show file information."""
    from luna.ui.theme import print_header
    
    file_path = Path(path).resolve()
    
    if not file_path.exists():
        console.print("[red]File not found[/]")
        return
    
    print_header("File Info", str(file_path))
    
    stat = file_path.stat()
    console.print(f"Path: {file_path}")
    console.print(f"Type: {'Directory' if file_path.is_dir() else 'File'}")
    console.print(f"Size: {stat.st_size} bytes")
    console.print(f"Modified: {file_path.stat().st_mtime}")
    console.print(f"Readable: {os.access(file_path, os.R_OK)}")
    console.print(f"Writable: {os.access(file_path, os.W_OK)}")


def main():
    """Main entry point."""
    files_app()


if __name__ == "__main__":
    files_app()
