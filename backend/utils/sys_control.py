import os
import subprocess
import shutil

class SystemController:
    """
    Abstractions for window, workspace, volume, and media management
    across various Linux environments.
    """
    def __init__(self):
        self.desktop = os.getenv("XDG_CURRENT_DESKTOP", "").lower()
        self.session_type = os.getenv("XDG_SESSION_TYPE", "").lower()
        print(f"[SystemController] Detected Desktop: {self.desktop}, Session Type: {self.session_type}")

    def execute_cmd(self, cmd: list) -> bool:
        """Executes a command and returns True if successful."""
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def switch_workspace(self, workspace_num: int) -> bool:
        """Switches to a specific workspace (1-indexed)."""
        # 1. Hyprland
        if "hyprland" in self.desktop or shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "workspace", str(workspace_num)])
        
        # 2. KDE Plasma
        if "kde" in self.desktop or shutil.which("qdbus"):
            return self.execute_cmd(["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.setCurrentDesktop", str(workspace_num)])
            
        # 3. GNOME (using D-Bus eval fallback or keyboard emulation if X11)
        if "gnome" in self.desktop:
            # We can use gdbus call to change workspace
            gdbus_cmd = [
                "gdbus", "call", "--session", 
                "--dest", "org.gnome.Shell", 
                "--object-path", "/org/gnome/Shell", 
                "--method", "org.gnome.Shell.Eval", 
                f"global.workspace_manager.get_workspace_by_index({workspace_num - 1}).activate(global.get_current_time());"
            ]
            if self.execute_cmd(gdbus_cmd):
                return True

        # 4. Generic X11 (using wmctrl)
        if shutil.which("wmctrl"):
            # wmctrl workspaces are 0-indexed
            return self.execute_cmd(["wmctrl", "-s", str(workspace_num - 1)])

        # 5. Keyboard simulation fallback
        if self.session_type == "x11" and shutil.which("xdotool"):
            return self.execute_cmd(["xdotool", "key", f"super+{workspace_num}"])
        elif shutil.which("wtype"):
            return self.execute_cmd(["wtype", "-M", "super", "-k", str(workspace_num)])

        return False

    def close_active_window(self) -> bool:
        """Closes the currently active window."""
        if "hyprland" in self.desktop or shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "killactive"])
            
        if shutil.which("xdotool") and self.session_type == "x11":
            return self.execute_cmd(["xdotool", "windowkill", "active"])
            
        if shutil.which("wmctrl"):
            return self.execute_cmd(["wmctrl", "-c", ":ACTIVE:"])

        return False

    def toggle_fullscreen(self) -> bool:
        """Toggles fullscreen on active window."""
        if "hyprland" in self.desktop or shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "fullscreen"])
            
        if shutil.which("xdotool") and self.session_type == "x11":
            return self.execute_cmd(["xdotool", "key", "F11"])
            
        if shutil.which("wmctrl"):
            return self.execute_cmd(["wmctrl", "-r", ":ACTIVE:", "-b", "toggle,fullscreen"])

        return False

    def set_volume(self, change: str) -> bool:
        """
        Adjusts system volume.
        change can be "5%+" or "5%-".
        """
        # 1. WirePlumber wpctl (modern standard)
        if shutil.which("wpctl"):
            direction = "+" if "+" in change else "-"
            # wpctl uses fractional values e.g. 0.05 for 5%
            return self.execute_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"0.05{direction}"])
            
        # 2. PulseAudio pactl
        if shutil.which("pactl"):
            prefix = "+" if "+" in change else "-"
            val = change.replace("+", "").replace("-", "")
            return self.execute_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{prefix}{val}"])
            
        # 3. ALSA amixer fallback
        if shutil.which("amixer"):
            val = "5%+" if "+" in change else "5%-"
            return self.execute_cmd(["amixer", "set", "Master", val])

        return False

    def control_media(self, action: str) -> bool:
        """
        Controls media playback.
        action can be "play", "pause", "play-pause", "next", "previous", "stop"
        """
        if shutil.which("playerctl"):
            return self.execute_cmd(["playerctl", action])
        return False

# Singleton instance
system_controller = SystemController()
