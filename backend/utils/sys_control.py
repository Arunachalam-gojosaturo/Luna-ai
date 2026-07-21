import os
import subprocess
import shutil
import time

class SystemController:
    """
    Abstractions for Arch Linux, Hyprland, Wayland, and audio/display/power controls.
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
        except Exception as e:
            print(f"[SystemController] Command {cmd} failed: {e}")
            return False

    def switch_workspace(self, workspace_num: int) -> bool:
        """Switches to a specific workspace (1-indexed)."""
        if "hyprland" in self.desktop or shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "workspace", str(workspace_num)])
        
        if "kde" in self.desktop or shutil.which("qdbus"):
            return self.execute_cmd(["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.setCurrentDesktop", str(workspace_num)])
            
        if "gnome" in self.desktop:
            gdbus_cmd = [
                "gdbus", "call", "--session", 
                "--dest", "org.gnome.Shell", 
                "--object-path", "/org/gnome/Shell", 
                "--method", "org.gnome.Shell.Eval", 
                f"global.workspace_manager.get_workspace_by_index({workspace_num - 1}).activate(global.get_current_time());"
            ]
            if self.execute_cmd(gdbus_cmd):
                return True

        if shutil.which("wmctrl"):
            return self.execute_cmd(["wmctrl", "-s", str(workspace_num - 1)])

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
        change can be "5%+" or "5%-", "up", "down", "mute".
        """
        if change in ["mute", "toggle_mute"]:
            return self.toggle_mute()

        direction = "+" if "+" in change or change == "up" else "-"
        amount = "5%"
        if "%" in change:
            amount = change.strip()

        # 1. WirePlumber wpctl (standard on modern Arch/Hyprland)
        if shutil.which("wpctl"):
            val = "0.05"
            if "10" in amount: val = "0.10"
            return self.execute_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val}{direction}"])
            
        # 2. PulseAudio pactl
        if shutil.which("pactl"):
            val_pct = "5%" if "5" in amount else "10%"
            return self.execute_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{direction}{val_pct}"])
            
        # 3. ALSA amixer fallback
        if shutil.which("amixer"):
            return self.execute_cmd(["amixer", "set", "Master", f"{amount}{direction}"])

        return False

    def toggle_mute(self) -> bool:
        """Toggles audio mute."""
        if shutil.which("wpctl"):
            return self.execute_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        if shutil.which("pactl"):
            return self.execute_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        if shutil.which("amixer"):
            return self.execute_cmd(["amixer", "set", "Master", "toggle"])
        return False

    def adjust_brightness(self, change: str) -> bool:
        """
        Adjusts display brightness.
        change can be "+10%", "-10%", "up", "down".
        """
        direction = "+" if "+" in change or change == "up" else "-"
        pct = "10%"
        if "%" in change:
            pct = change.replace("+", "").replace("-", "").strip()

        if shutil.which("brightnessctl"):
            return self.execute_cmd(["brightnessctl", "set", f"{pct}{direction}"])
        if shutil.which("light"):
            flag = "-A" if direction == "+" else "-U"
            val = pct.replace("%", "")
            return self.execute_cmd(["light", flag, val])
        return False

    def power_action(self, action: str) -> bool:
        """Handles Linux system power management (shutdown, reboot, suspend, lock)."""
        action = action.lower().strip()
        if action in ["shutdown", "poweroff"]:
            return self.execute_cmd(["systemctl", "poweroff"])
        elif action in ["reboot", "restart"]:
            return self.execute_cmd(["systemctl", "reboot"])
        elif action in ["suspend", "sleep"]:
            return self.execute_cmd(["systemctl", "suspend"])
        elif action in ["lock", "lockscreen"]:
            if shutil.which("hyprlock"):
                return self.execute_cmd(["hyprlock"])
            elif shutil.which("swaylock"):
                return self.execute_cmd(["swaylock"])
            else:
                return self.execute_cmd(["loginctl", "lock-session"])
        return False

    def take_screenshot(self) -> bool:
        """Takes a full screen screenshot and saves to ~/Pictures."""
        pictures_dir = os.path.expanduser("~/Pictures")
        os.makedirs(pictures_dir, exist_ok=True)
        filename = f"{pictures_dir}/screenshot_{int(time.time())}.png"

        if shutil.which("hyprshot"):
            return self.execute_cmd(["hyprshot", "-m", "output", "-o", pictures_dir, "-f", os.path.basename(filename)])
        if shutil.which("grim"):
            return self.execute_cmd(["grim", filename])
        if shutil.which("maim"):
            return self.execute_cmd(["maim", filename])
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
