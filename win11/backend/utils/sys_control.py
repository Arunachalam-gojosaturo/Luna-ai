import os
import sys
import subprocess
import shutil
import time
import platform

class SystemController:
    """
    Abstractions for Windows 11 & Linux desktop system controls (audio, display, power, media).
    """
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.desktop = "windows11" if self.is_windows else os.getenv("XDG_CURRENT_DESKTOP", "").lower()
        print(f"[SystemController] Detected Platform: {platform.system()}, Desktop: {self.desktop}")

    def execute_cmd(self, cmd: list) -> bool:
        """Executes a command and returns True if successful."""
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[SystemController] Command {cmd} failed: {e}")
            return False

    def execute_ps(self, ps_script: str) -> bool:
        """Executes a PowerShell script block on Windows."""
        try:
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[SystemController] PowerShell script failed: {e}")
            return False

    def switch_workspace(self, workspace_num: int) -> bool:
        """Switches to a specific virtual desktop / workspace."""
        if self.is_windows:
            # Send Win+Ctrl+Left/Right on Windows 11
            ps = f"$w = New-Object -ComObject WScript.Shell; 1..{workspace_num} | % {{ $w.SendKeys('^#{{RIGHT}}') }}"
            return self.execute_ps(ps)
        
        if "hyprland" in self.desktop or shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "workspace", str(workspace_num)])
        return False

    def close_active_window(self) -> bool:
        """Closes the currently active window."""
        if self.is_windows:
            return self.execute_ps("(New-Object -ComObject WScript.Shell).SendKeys('%{F4}')")
        if shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "killactive"])
        return False

    def toggle_fullscreen(self) -> bool:
        """Toggles fullscreen on active window."""
        if self.is_windows:
            return self.execute_ps("(New-Object -ComObject WScript.Shell).SendKeys('{F11}')")
        if shutil.which("hyprctl"):
            return self.execute_cmd(["hyprctl", "dispatch", "fullscreen"])
        return False

    def set_volume(self, change: str) -> bool:
        """Adjusts system volume."""
        if change in ["mute", "toggle_mute"]:
            return self.toggle_mute()

        if self.is_windows:
            key = "[char]175" if "+" in change or change == "up" else "[char]174"
            return self.execute_ps(f"1..3 | % {{ (New-Object -ComObject WScript.Shell).SendKeys({key}) }}")

        if shutil.which("wpctl"):
            direction = "+" if "+" in change or change == "up" else "-"
            return self.execute_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"0.05{direction}"])
        return False

    def toggle_mute(self) -> bool:
        """Toggles audio mute."""
        if self.is_windows:
            return self.execute_ps("(New-Object -ComObject WScript.Shell).SendKeys([char]173)")
        if shutil.which("wpctl"):
            return self.execute_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        return False

    def adjust_brightness(self, change: str) -> bool:
        """Adjusts display brightness."""
        if self.is_windows:
            delta = 10 if "+" in change or change == "up" else -10
            ps = f"$b = (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness; $newB = [math]::Max(0, [math]::Min(100, $b + ({delta}))); (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, $newB)"
            return self.execute_ps(ps)
        if shutil.which("brightnessctl"):
            return self.execute_cmd(["brightnessctl", "set", "10%+"])
        return False

    def power_action(self, action: str) -> bool:
        """Handles Windows 11 system power management (shutdown, reboot, suspend, lock)."""
        action = action.lower().strip()
        if self.is_windows:
            if action in ["shutdown", "poweroff"]:
                return self.execute_cmd(["shutdown", "/s", "/t", "5"])
            elif action in ["reboot", "restart"]:
                return self.execute_cmd(["shutdown", "/r", "/t", "5"])
            elif action in ["suspend", "sleep"]:
                return self.execute_cmd(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            elif action in ["lock", "lockscreen"]:
                return self.execute_cmd(["rundll32.exe", "user32.dll,LockWorkStation"])
        else:
            if action in ["shutdown", "poweroff"]:
                return self.execute_cmd(["systemctl", "poweroff"])
            elif action in ["reboot", "restart"]:
                return self.execute_cmd(["systemctl", "reboot"])
            elif action in ["lock", "lockscreen"]:
                return self.execute_cmd(["loginctl", "lock-session"])
        return False

    def take_screenshot(self) -> bool:
        """Takes a full screen screenshot and saves to Pictures folder."""
        pictures_dir = os.path.expanduser("~/Pictures")
        os.makedirs(pictures_dir, exist_ok=True)
        filename = os.path.join(pictures_dir, f"screenshot_{int(time.time())}.png").replace("\\", "/")

        if self.is_windows:
            ps = f"Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $img = New-Object System.Drawing.Bitmap($b.Width, $b.Height); $g = [System.Drawing.Graphics]::FromImage($img); $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); $img.Save('{filename}'); $g.Dispose(); $img.Dispose()"
            return self.execute_ps(ps)
        if shutil.which("grim"):
            return self.execute_cmd(["grim", filename])
        return False

    def control_media(self, action: str) -> bool:
        """Controls media playback."""
        if self.is_windows:
            key_map = {
                "play": "[char]179", "pause": "[char]179", "play-pause": "[char]179",
                "next": "[char]176", "previous": "[char]177", "stop": "[char]178"
            }
            vk = key_map.get(action.lower(), "[char]179")
            return self.execute_ps(f"(New-Object -ComObject WScript.Shell).SendKeys({vk})")
        if shutil.which("playerctl"):
            return self.execute_cmd(["playerctl", action])
        return False

# Singleton instance
system_controller = SystemController()
