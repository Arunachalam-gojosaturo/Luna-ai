"""
Luna Task Engine — system-level operations:
  • Create files / directories
  • Write code to files
  • Open editor (nano / micro / kate)
  • Run shell commands
  • Download music via yt-dlp
  • Package installation
"""
import os
import re
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime


class TaskResult:
    def __init__(self, success: bool, message: str, output: str = ""):
        self.success = success
        self.message = message
        self.output  = output

    def __str__(self):
        return self.message


class TaskEngine:
    def __init__(self, mem):
        self.mem = mem

    @property
    def workspace(self) -> Path:
        d = Path(self.mem.get("workspace_dir", str(Path.home() / "LunaWorkspace")))
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def download_dir(self) -> Path:
        d = Path(self.mem.get("download_dir", str(Path.home() / "Music")))
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ── Dispatch ──────────────────────────────────────────────────────────
    def handle(self, text: str) -> TaskResult | None:
        """Return TaskResult if text is a system task, else None."""
        t = text.strip()
        tl = t.lower()

        # Create directory
        m = re.search(r"create\s+(?:a\s+)?(?:dir(?:ectory)?|folder)\s+(?:named?\s+|called?\s+)?['\"]?(\S+)['\"]?", tl)
        if m:
            return self.create_dir(m.group(1))

        # Create file
        m = re.search(r"create\s+(?:a\s+)?file\s+(?:named?\s+|called?\s+)?['\"]?([\w\.\-]+)['\"]?", tl)
        if m:
            return self.create_file(m.group(1))

        # Write/save code to file
        m = re.search(r"(?:write|save|put)\s+(?:code|script|this)\s+(?:to|in(?:to)?)\s+['\"]?([\w\.\-/]+)['\"]?", tl)
        if m:
            return self.open_editor(m.group(1))

        # Open file in editor
        m = re.search(r"(?:open|edit)\s+['\"]?([\w\.\-/]+)['\"]?\s+(?:in\s+)?(?:editor|nano|micro)?", tl)
        if m and ("open" in tl or "edit" in tl):
            return self.open_editor(m.group(1))

        # Run command
        m = re.search(r"^(?:run|execute|shell|cmd)\s+(.+)$", t, re.IGNORECASE)
        if m:
            return self.run_command(m.group(1))

        # Download music/song
        m = re.search(r"download\s+(?:song|music|audio|track|video)?\s*['\"]?(.+?)['\"]?\s*$", t, re.IGNORECASE)
        if m:
            return self.download_music(m.group(1).strip())

        # Install package
        m = re.search(r"install\s+(?:package\s+|app\s+)?(\S+)", tl)
        if m:
            return self.install_package(m.group(1))

        # List workspace
        if re.search(r"(?:list|show|ls)\s+(?:files?|workspace|dir)", tl):
            return self.list_workspace()

        return None

    # ── Operations ────────────────────────────────────────────────────────
    def create_dir(self, name: str) -> TaskResult:
        try:
            target = self.workspace / name
            target.mkdir(parents=True, exist_ok=True)
            return TaskResult(True, f"Directory created: `{target}`")
        except Exception as e:
            return TaskResult(False, f"Failed to create directory: {e}")

    def create_file(self, name: str, content: str = "") -> TaskResult:
        try:
            target = self.workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return TaskResult(True, f"File created: `{target}`", output=str(target))
        except Exception as e:
            return TaskResult(False, f"Failed to create file: {e}")

    def write_code_to_file(self, filename: str, code: str, lang: str = "") -> TaskResult:
        """Write code block to file in workspace."""
        # Add extension if missing
        if "." not in filename:
            ext_map = {"python": ".py", "py": ".py", "javascript": ".js",
                       "js": ".js", "bash": ".sh", "sh": ".sh",
                       "html": ".html", "css": ".css", "rust": ".rs",
                       "go": ".go", "java": ".java", "cpp": ".cpp"}
            filename += ext_map.get(lang.lower(), ".txt")

        try:
            target = self.workspace / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code)
            if filename.endswith(".sh"):
                os.chmod(target, 0o755)
            return TaskResult(True, f"Code saved to `{target}`", output=str(target))
        except Exception as e:
            return TaskResult(False, f"Failed to write code: {e}")

    def open_editor(self, filename: str) -> TaskResult:
        """Open file in terminal editor."""
        target = self.workspace / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.touch()

        for editor in ["micro", "nano", "vim", "vi"]:
            if shutil.which(editor):
                try:
                    subprocess.Popen(
                        ["x-terminal-emulator", "-e", f"{editor} {target}"],
                        start_new_session=True
                    )
                    return TaskResult(True, f"Opened `{target.name}` in {editor}.")
                except FileNotFoundError:
                    # try direct terminal
                    for term in ["konsole", "gnome-terminal", "xterm", "alacritty", "kitty"]:
                        if shutil.which(term):
                            arg = f"--hold -e" if "xterm" in term else "-e"
                            subprocess.Popen(
                                [term, "-e", f"{editor}", str(target)],
                                start_new_session=True
                            )
                            return TaskResult(True, f"Opened `{target.name}` in {editor}.")
        return TaskResult(False, "No terminal editor found (nano, micro, vim).")

    def run_command(self, cmd: str) -> TaskResult:
        """Run a shell command."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=str(self.workspace)
            )
            out = (result.stdout + result.stderr).strip()
            success = result.returncode == 0
            return TaskResult(success, f"Command {'succeeded' if success else 'failed'}.", output=out)
        except subprocess.TimeoutExpired:
            return TaskResult(False, "Command timed out after 30s.")
        except Exception as e:
            return TaskResult(False, f"Command error: {e}")

    def download_music(self, query: str) -> TaskResult:
        """Download audio via yt-dlp."""
        self._ensure_ytdlp()
        out_dir = self.download_dir
        try:
            cmd = [
                sys.executable, "-m", "yt_dlp",
                f"ytsearch1:{query}",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-thumbnail",
                "--add-metadata",
                "-o", str(out_dir / "%(title)s.%(ext)s"),
                "--no-playlist",
                "--quiet",
                "--progress",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                # Find latest file
                files = sorted(out_dir.glob("*.mp3"), key=os.path.getmtime, reverse=True)
                fname = files[0].name if files else "unknown"
                return TaskResult(True, f"Downloaded: **{fname}** → `{out_dir}`")
            else:
                err = (result.stderr or result.stdout)[:300]
                return TaskResult(False, f"Download failed: {err}")
        except subprocess.TimeoutExpired:
            return TaskResult(False, "Download timed out (120s).")
        except Exception as e:
            return TaskResult(False, f"Download error: {e}")

    def install_package(self, name: str) -> TaskResult:
        """Install Python package or system package."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", name, "-q"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return TaskResult(True, f"Installed Python package: `{name}`")
            # Try pacman
            result2 = subprocess.run(
                ["sudo", "pacman", "-S", name, "--noconfirm"],
                capture_output=True, text=True, timeout=60
            )
            if result2.returncode == 0:
                return TaskResult(True, f"Installed system package: `{name}`")
            return TaskResult(False, f"Could not install `{name}`. Try manually.")
        except Exception as e:
            return TaskResult(False, f"Install error: {e}")

    def list_workspace(self) -> TaskResult:
        """List files in workspace."""
        files = list(self.workspace.rglob("*"))
        if not files:
            return TaskResult(True, f"Workspace `{self.workspace}` is empty.")
        lines = []
        for f in sorted(files)[:40]:
            rel = f.relative_to(self.workspace)
            icon = "📁" if f.is_dir() else "📄"
            lines.append(f"{icon} {rel}")
        output = "\n".join(lines)
        return TaskResult(True, f"Workspace contents ({len(files)} items):", output=output)

    # ── Helpers ───────────────────────────────────────────────────────────
    def _ensure_ytdlp(self):
        try:
            import yt_dlp  # noqa
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"],
                           capture_output=True, timeout=60)
