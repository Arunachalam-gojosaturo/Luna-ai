import asyncio
import datetime
import psutil
import shlex
import re

from backend.agents.base_agent import BaseAgent

class LinuxAgent(BaseAgent):
    def __init__(self):
        self.os_type = "arch" # Designed specifically for Arch Linux & Hyprland
        from backend.config.paths import get_log_dir
        self.audit_log_path = str(get_log_dir() / "luna_audit.log")
        
        # Complete allowed commands whitelist for Linux System & Mobile ADB
        self.allowed_commands = [
            "ls", "cat", "pwd", "cd", "echo", "mkdir", "touch", "cp", "mv", "rm",
            "find", "grep", "git", "pip", "npm", "python", "node", "curl", "wget",
            "systemctl", "sudo", "pacman", "apt", "yum", "docker", "docker-compose",
            "tmux", "screen", "less", "more", "head", "tail", "wc", "chmod", "chown",
            "ps", "kill", "df", "du", "free", "top", "htop", "uname", "whoami", "xdg-open", "open",
            "playerctl", "hyprctl", "wpctl", "pactl", "amixer", "brightnessctl", "light",
            "ydotool", "wtype", "yay", "paru", "adb", "scrcpy", "grim", "slurp", "hyprshot",
            "loginctl", "hyprlock", "swaylock", "poweroff", "reboot", "shutdown", "rofi", "kitty"
        ]
        
    def append_audit_log(self, command: str, intent: str, sys_command: str, privilege: bool):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] INTENT: {intent} | PRIVILEGE: {privilege} | CMD: {command} | EXEC: {sys_command}\n"
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(log_entry)
        except Exception:
            pass

    def validate_command(self, command: str):
        """Validate command for safety - check against dangerous patterns."""
        dangerous_patterns = [
            r"rm\s+-.*rf\s+/",  # rm -rf / style commands
            r"dd\s+if=.*of=/dev/[a-z]+",  # dd commands targeting devices
            r":\(\)\s*{\s*:\|:\s*&\s*};\s*:",  # fork bomb
            r">\s*/dev/[a-z]+",  # redirects to devices
            r";\s*rm\s+",  # chained rm commands
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {"allowed": False, "reason": "Dangerous command pattern detected"}
        
        cmd_parts = shlex.split(command) if command else []
        if cmd_parts:
            base_cmd = cmd_parts[0].split('/')[-1]
            if base_cmd not in self.allowed_commands and not command.startswith("sudo"):
                return {"allowed": False, "reason": f"Command '{base_cmd}' not in allowed list"}
        
        return {"allowed": True, "wrappedCommand": command}

    async def execute(self, command: str, category: str = "RAW_COMMAND"):
        self.append_audit_log(command, category, command, "sudo" in command or "pkexec" in command)
        
        from backend.utils.sys_control import system_controller
        from backend.utils.adb_manager import adb_manager
        
        cmd_lower = command.lower().strip()

        # 0. Chained shell commands (e.g. "hyprctl dispatch workspace 2 && hyprctl dispatch exec code .")
        if "&&" in command or ";" in command:
            sub_cmds = [c.strip() for c in re.split(r"&&|;", command) if c.strip()]
            outputs = []
            all_ok = True
            for sub in sub_cmds:
                sub_res = await self.execute(sub, category)
                if sub_res.get("stdout"):
                    outputs.append(sub_res["stdout"])
                if not sub_res.get("success", False):
                    all_ok = False
            return {"success": all_ok, "stdout": "\n".join(outputs), "stderr": ""}

        # 1. Mobile Lock, Unlock, PIN Update & App Launch Interceptors
        pin_update_match = re.search(r"(?:change|set|update|remember)\s+(?:mobile|phone)\s+(?:pin|password)\s+(?:to\s+)?(\d+)", cmd_lower) or re.search(r"(?:pin|password)\s+is\s+(\d+)", cmd_lower)
        if pin_update_match:
            new_pin = pin_update_match.group(1)
            adb_manager.set_mobile_pin(new_pin)
            return {"success": True, "stdout": f"Updated mobile unlock PIN to {new_pin}", "stderr": ""}

        if "unlock" in cmd_lower and ("mobile" in cmd_lower or "phone" in cmd_lower or "device" in cmd_lower or "android" in cmd_lower):
            pin_specified = re.search(r"\b(\d{4,8})\b", command)
            pin_val = pin_specified.group(1) if pin_specified else None
            res = await adb_manager.unlock_device(pin=pin_val)
            return {"success": res["status"] == "success", "stdout": res.get("result", "Unlocked mobile"), "stderr": res.get("stderr", "")}

        if "lock" in cmd_lower and ("mobile" in cmd_lower or "phone" in cmd_lower or "device" in cmd_lower or "android" in cmd_lower) and "session" not in cmd_lower:
            res = await adb_manager.lock_device()
            return {"success": res["status"] == "success", "stdout": res.get("result", "Locked mobile"), "stderr": res.get("stderr", "")}

        if "whatsapp" in cmd_lower and ("open" in cmd_lower or "start" in cmd_lower or "launch" in cmd_lower or "mobile" in cmd_lower):
            res = await adb_manager.launch_app("whatsapp")
            return {"success": res["status"] == "success", "stdout": res.get("result", "Launched WhatsApp"), "stderr": res.get("stderr", "")}

        mobile_app_match = re.search(r"(?:open|launch|start)\s+(\w+)\s+(?:on|in)\s+(?:mobile|phone|android)", cmd_lower)
        if mobile_app_match:
            app_name = mobile_app_match.group(1)
            res = await adb_manager.launch_app(app_name)
            return {"success": res["status"] == "success", "stdout": res.get("result", f"Launched {app_name}"), "stderr": res.get("stderr", "")}

        # 2. System Power Actions (Shutdown, Reboot, Suspend, Lock)
        if "poweroff" in cmd_lower or "shutdown" in cmd_lower:
            success = system_controller.power_action("shutdown")
            return {"success": success, "stdout": "Initiating system shutdown...", "stderr": ""}
        if "reboot" in cmd_lower or "restart" in cmd_lower:
            success = system_controller.power_action("reboot")
            return {"success": success, "stdout": "Initiating system reboot...", "stderr": ""}
        if "suspend" in cmd_lower or "sleep" in cmd_lower:
            success = system_controller.power_action("suspend")
            return {"success": success, "stdout": "Suspending system...", "stderr": ""}
        if "lockscreen" in cmd_lower or "lock screen" in cmd_lower or ("lock" in cmd_lower and "session" in cmd_lower):
            success = system_controller.power_action("lock")
            return {"success": success, "stdout": "Locking screen...", "stderr": ""}

        # 3. Brightness Control
        bright_match = re.search(r"brightness(?:ctl)?\s+(?:set\s+)?([+\-]?\d+%?)", cmd_lower) or re.search(r"(increase|decrease|up|down)\s+brightness", cmd_lower)
        if bright_match:
            val = bright_match.group(1) if len(bright_match.groups()) == 1 and bright_match.group(1) else ("+10%" if "increase" in cmd_lower or "up" in cmd_lower else "-10%")
            success = system_controller.adjust_brightness(val)
            return {"success": success, "stdout": f"Brightness adjusted: {val}", "stderr": ""}

        # 4. Volume & Mute Control
        vol_match = re.search(r"set-volume.*([\d%+-]+)", cmd_lower) or re.search(r"amixer.*set.*Master.*([\d%+-]+)", cmd_lower) or re.search(r"(volume|sound)\s+(up|down|mute|unmute|\d+%)", cmd_lower)
        if vol_match:
            change = vol_match.group(1) if len(vol_match.groups()) == 1 else vol_match.group(2)
            success = system_controller.set_volume(change)
            return {"success": success, "stdout": f"Volume adjusted: {change}", "stderr": ""}

        # 5. Screenshot
        if "screenshot" in cmd_lower or "hyprshot" in cmd_lower or "grim" in cmd_lower:
            success = system_controller.take_screenshot()
            return {"success": success, "stdout": "Screenshot captured and saved to ~/Pictures", "stderr": ""}

        # 6. Compound Workspace + App Launching or Workspace switching
        ws_match = re.search(r"workspace\s+(\d+)", command) or re.search(r"wmctrl\s+-s\s+(\d+)", command)
        app_in_cmd = None
        if "code" in cmd_lower or "vscode" in cmd_lower:
            app_in_cmd = "code ."
        elif "firefox" in cmd_lower or "browser" in cmd_lower:
            app_in_cmd = "firefox"
        elif "terminal" in cmd_lower or "kitty" in cmd_lower:
            app_in_cmd = "kitty"

        if ws_match:
            num = int(ws_match.group(1))
            if "wmctrl" in command:
                num += 1
            system_controller.switch_workspace(num)
            
            if app_in_cmd:
                await asyncio.sleep(0.3)
                launch_cmd = f"hyprctl dispatch exec {app_in_cmd}" if "hyprland" in system_controller.desktop else app_in_cmd
                await asyncio.create_subprocess_shell(launch_cmd)
                return {"success": True, "stdout": f"Switched to workspace {num} and launched {app_in_cmd}", "stderr": ""}
            return {"success": True, "stdout": f"Switched to workspace {num}", "stderr": ""}

        # 7. Close Active Window
        if "killactive" in command or "windowkill" in command or "wmctrl -c" in command:
            success = system_controller.close_active_window()
            return {"success": success, "stdout": "Closed active window", "stderr": ""}

        # 8. Fullscreen
        if "fullscreen" in command:
            success = system_controller.toggle_fullscreen()
            return {"success": success, "stdout": "Toggled fullscreen", "stderr": ""}

        # 9. Media Control
        media_match = re.search(r"playerctl\s+(\w+)", command)
        if media_match:
            action = media_match.group(1)
            success = system_controller.control_media(action)
            return {"success": success, "stdout": f"Media command: {action}", "stderr": ""}

        val = self.validate_command(command)
        if not val or not val.get("allowed", False):
            return {"success": False, "stdout": "", "stderr": val.get("reason", "Command validation failed") if val else "Invalid validation response"}
        
        try:
            proc = await asyncio.create_subprocess_shell(
                val["wrappedCommand"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=8.0)
                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else ""
                }
            except asyncio.TimeoutError:
                return {
                    "success": True,
                    "stdout": "Command started in background",
                    "stderr": ""
                }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}

    def get_metrics(self):
        return {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent
        }
        
    async def verify(self, execution_result: dict) -> bool:
        return execution_result.get("success", False)
