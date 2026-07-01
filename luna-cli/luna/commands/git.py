"""
Git integration command.
Handles git operations and integration.
"""

import typer
from rich.console import Console
from rich.syntax import Syntax
from typing import Optional
from pathlib import Path
import subprocess

console = Console()

git_app = typer.Typer(help="Git operations")


def run_git_command(cmd: list) -> tuple[bool, str]:
    """Run git command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout or result.stderr
    except Exception as e:
        return False, str(e)


@git_app.command(name="status")
def git_status():
    """Show git status."""
    from luna.ui.theme import print_header, print_status
    
    print_header("Git Status")
    success, output = run_git_command(["git", "status", "--short"])
    
    if success:
        if output:
            console.print(output)
        else:
            print_status("Working directory clean", "success")
    else:
        print_status("Error: Not a git repository", "error")


@git_app.command(name="log")
def git_log(
    limit: int = typer.Option(10, "-n", "--number", help="Number of commits"),
    oneline: bool = typer.Option(True, "--oneline/--full", help="Format"),
):
    """Show git log."""
    from luna.ui.theme import print_header
    
    print_header("Git Log")
    cmd = ["git", "log", f"-{limit}"]
    if oneline:
        cmd.append("--oneline")
    
    success, output = run_git_command(cmd)
    if success:
        console.print(output)
    else:
        from luna.ui.theme import print_status
        print_status("Error reading git log", "error")


@git_app.command(name="diff")
def git_diff(
    staged: bool = typer.Option(False, "--staged", help="Show staged changes"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Specific file"),
):
    """Show git diff."""
    from luna.ui.theme import print_header
    
    print_header("Git Diff")
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    if file:
        cmd.append(file)
    
    success, output = run_git_command(cmd)
    if success and output:
        # Try to syntax highlight the diff
        try:
            syntax = Syntax(output, "diff", theme="monokai", line_numbers=True)
            console.print(syntax)
        except:
            console.print(output)
    else:
        from luna.ui.theme import print_status
        print_status("No changes to show", "info")


@git_app.command(name="commit")
def git_commit(
    message: str = typer.Argument(help="Commit message"),
    all_changes: bool = typer.Option(False, "-a", "--all", help="Stage all changes"),
):
    """Create git commit."""
    from luna.ui.theme import print_success, print_error
    
    if all_changes:
        run_git_command(["git", "add", "-A"])
    
    success, output = run_git_command(["git", "commit", "-m", message])
    
    if success:
        print_success("Commit Created", output.split("\n")[0])
    else:
        print_error("Commit Failed", output)


@git_app.command(name="branch")
def git_branch(
    create: Optional[str] = typer.Option(None, "-c", "--create", help="Create branch"),
    delete: Optional[str] = typer.Option(None, "-d", "--delete", help="Delete branch"),
    list_branches: bool = typer.Option(False, "-l", "--list", help="List branches"),
):
    """Git branch operations."""
    from luna.ui.theme import print_header, print_success, print_error
    
    if create:
        success, output = run_git_command(["git", "branch", create])
        if success:
            print_success("Branch Created", f"Created branch: {create}")
        else:
            print_error("Failed", output)
    
    elif delete:
        success, output = run_git_command(["git", "branch", "-d", delete])
        if success:
            print_success("Branch Deleted", f"Deleted branch: {delete}")
        else:
            print_error("Failed", output)
    
    else:
        print_header("Git Branches")
        success, output = run_git_command(["git", "branch", "-v"])
        if success:
            console.print(output)


@git_app.command(name="push")
def git_push(
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to push"),
):
    """Push changes to remote."""
    from luna.ui.theme import print_status
    
    cmd = ["git", "push"]
    if branch:
        cmd.append(branch)
    
    success, output = run_git_command(cmd)
    if success:
        print_status("Push successful", "success")
    else:
        print_status(f"Push failed: {output}", "error")


@git_app.command(name="pull")
def git_pull():
    """Pull changes from remote."""
    from luna.ui.theme import print_status
    
    success, output = run_git_command(["git", "pull"])
    if success:
        print_status("Pull successful", "success")
    else:
        print_status(f"Pull failed: {output}", "error")


def main():
    """Main entry point."""
    git_app()


if __name__ == "__main__":
    git_app()
