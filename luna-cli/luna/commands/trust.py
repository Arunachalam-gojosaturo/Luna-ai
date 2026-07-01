"""
Trust and permissions management command.
Manage trusted workspaces and execution permissions.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json
import platformdirs

console = Console()

trust_app = typer.Typer(help="Manage trusted workspaces")


class TrustManager:
    """Manage trusted workspaces."""
    
    CONFIG_DIR = Path(platformdirs.user_config_dir("luna", "luna"))
    TRUST_FILE = CONFIG_DIR / "trusted_workspaces.json"
    
    def __init__(self):
        """Initialize trust manager."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.trusted = self._load_trusted()
    
    def _load_trusted(self) -> dict:
        """Load trusted workspaces."""
        if self.TRUST_FILE.exists():
            try:
                with open(self.TRUST_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_trusted(self):
        """Save trusted workspaces."""
        with open(self.TRUST_FILE, 'w') as f:
            json.dump(self.trusted, f, indent=2)
    
    def trust_workspace(self, path: str, level: str = "execute"):
        """Trust a workspace."""
        path = str(Path(path).resolve())
        self.trusted[path] = {
            "level": level,
            "trusted_at": __import__("datetime").datetime.now().isoformat()
        }
        self._save_trusted()
        return path
    
    def untrust_workspace(self, path: str):
        """Remove trust from workspace."""
        path = str(Path(path).resolve())
        if path in self.trusted:
            del self.trusted[path]
            self._save_trusted()
            return True
        return False
    
    def is_trusted(self, path: str, level: str = "execute") -> bool:
        """Check if workspace is trusted."""
        path = str(Path(path).resolve())
        return path in self.trusted and self.trusted[path]["level"] == level
    
    def list_trusted(self) -> dict:
        """List all trusted workspaces."""
        return self.trusted


@trust_app.command(name="add")
def trust_workspace(
    path: str = typer.Argument(".", help="Workspace path"),
    level: str = typer.Option("execute", "--level", "-l", help="Trust level: ask, execute, full"),
):
    """Trust a workspace for command execution."""
    from luna.ui.theme import print_success, print_error
    
    mgr = TrustManager()
    resolved = mgr.trust_workspace(path, level)
    print_success("Workspace Trusted", f"Workspace added to trusted list:\n{resolved}")


@trust_app.command(name="remove")
def untrust_workspace(path: str = typer.Argument(".", help="Workspace path")):
    """Remove workspace from trusted list."""
    from luna.ui.theme import print_success, print_error
    
    mgr = TrustManager()
    path = str(Path(path).resolve())
    
    if mgr.untrust_workspace(path):
        print_success("Workspace Removed", f"Workspace removed from trusted list")
    else:
        print_error("Not Found", f"Workspace not in trusted list")


@trust_app.command(name="list")
def list_trusted():
    """List all trusted workspaces."""
    mgr = TrustManager()
    trusted = mgr.list_trusted()
    
    if not trusted:
        console.print("[yellow]No trusted workspaces[/]")
        return
    
    table = Table(title="Trusted Workspaces", show_header=True, header_style="bold cyan")
    table.add_column("Path", style="cyan")
    table.add_column("Level", style="yellow")
    table.add_column("Trusted At", style="dim")
    
    for path, info in trusted.items():
        table.add_row(path, info.get("level", "execute"), info.get("trusted_at", "—"))
    
    console.print(table)


@trust_app.command(name="check")
def check_trust(path: str = typer.Argument(".", help="Workspace path")):
    """Check if workspace is trusted."""
    from luna.ui.theme import print_status
    
    mgr = TrustManager()
    resolved_path = str(Path(path).resolve())
    
    if mgr.is_trusted(resolved_path):
        print_status(f"✓ Workspace is trusted: {resolved_path}", "success")
    else:
        print_status(f"✗ Workspace is not trusted: {resolved_path}", "warning")


def main():
    """Main entry point."""
    trust_app()


if __name__ == "__main__":
    trust_app()
