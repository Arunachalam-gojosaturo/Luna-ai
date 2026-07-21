import os
import re
import json
import asyncio
import subprocess
from typing import List, Dict, Optional
from backend.config.paths import get_config_dir

SAVED_DEVICES_FILE = get_config_dir() / "saved_adb_devices.json"

class ADBManager:
    """
    Automated ADB Manager:
    - Scans connected ADB devices (USB & Wireless)
    - Auto-detects Wi-Fi IP of USB-connected Android phones
    - Configures Wireless TCP/IP ONCE per USB connection
    - Remembers devices in saved_adb_devices.json
    - Reconnects saved wireless devices cleanly without causing connection drops
    - Provides high-level mobile controls (WhatsApp, apps, keyevents, tap, text)
    """

    def __init__(self):
        self._configured_serials = set()
        self._ensure_config()

    def _ensure_config(self):
        if not SAVED_DEVICES_FILE.exists():
            try:
                with open(SAVED_DEVICES_FILE, "w") as f:
                    json.dump({}, f, indent=2)
            except Exception as e:
                print(f"[ADBManager] Could not create saved devices file: {e}")

    def load_saved_devices(self) -> Dict[str, dict]:
        try:
            if SAVED_DEVICES_FILE.exists():
                with open(SAVED_DEVICES_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[ADBManager] Error loading saved devices: {e}")
        return {}

    def save_device_info(self, key: str, info: dict):
        try:
            saved = self.load_saved_devices()
            saved[key] = info
            with open(SAVED_DEVICES_FILE, "w") as f:
                json.dump(saved, f, indent=2)
        except Exception as e:
            print(f"[ADBManager] Failed to save device info: {e}")

    async def get_device_ip(self, serial: str) -> Optional[str]:
        """Attempt multiple methods to retrieve the Wi-Fi IP of an Android device over USB."""
        # Method 1: getprop dhcp.wlan0.ipaddress
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            ip = stdout.decode().strip()
            if ip and not ip.endswith(".0") and not ip.endswith(".255") and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip
        except Exception:
            pass

        # Method 2: ip route (look for 'src X.X.X.X')
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "ip", "route",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode().strip()
            src_match = re.search(r"src\s+((?:\d{1,3}\.){3}\d{1,3})", out)
            if src_match:
                ip = src_match.group(1)
                if not ip.endswith(".0") and not ip.endswith(".255"):
                    return ip
        except Exception:
            pass

        # Method 3: ip addr show wlan0
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode().strip()
            inet_match = re.search(r"inet\s+((?:\d{1,3}\.){3}\d{1,3})", out)
            if inet_match:
                ip = inet_match.group(1)
                if not ip.endswith(".0") and not ip.endswith(".255") and not ip.startswith("127."):
                    return ip
        except Exception:
            pass

        return None

    async def scan_and_auto_connect(self) -> List[dict]:
        """
        Scan devices safely without continuously restarting tcpip on every poll.
        """
        devices = []
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "devices", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            lines = stdout.decode().strip().split("\n")
            
            has_offline = False
            if len(lines) > 1:
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        serial = parts[0]
                        status = parts[1]
                        model = "Android Device"
                        for p in parts[2:]:
                            if p.startswith("model:"):
                                model = p.split("model:")[1]
                            elif p.startswith("device:"):
                                model = p.split("device:")[1]

                        if status == "offline":
                            has_offline = True

                        is_wireless = ":" in serial
                        device_entry = {
                            "serial": serial,
                            "status": status,
                            "model": model,
                            "is_wireless": is_wireless
                        }
                        devices.append(device_entry)

                        # Auto-detect IP for USB connected device once
                        if not is_wireless and status == "device" and serial not in self._configured_serials:
                            ip = await self.get_device_ip(serial)
                            if ip:
                                device_entry["ip"] = ip
                                self.save_device_info(serial, {
                                    "serial": serial,
                                    "model": model,
                                    "ip": ip,
                                    "port": "5555"
                                })
                                self._configured_serials.add(serial)

            # If an offline wireless device is detected, reconnect cleanly
            if has_offline:
                saved = self.load_saved_devices()
                for dkey, info in saved.items():
                    ip = info.get("ip")
                    if ip:
                        # disconnect offline target
                        await (await asyncio.create_subprocess_exec("adb", "disconnect", f"{ip}:5555")).communicate()
                        await (await asyncio.create_subprocess_exec("adb", "connect", f"{ip}:5555")).communicate()

        except Exception as e:
            print(f"[ADBManager] Error scanning ADB devices: {e}")

        return devices

    async def launch_scrcpy(self, target: str = "") -> dict:
        """Safely launch scrcpy window."""
        try:
            # Check devices first
            devices = await self.scan_and_auto_connect()
            online_device = None
            
            for d in devices:
                if d["status"] == "device":
                    if not target or target in d["serial"] or target in d.get("ip", ""):
                        online_device = d["serial"]
                        break
            
            cmd = ["scrcpy"]
            if online_device:
                cmd.extend(["-s", online_device])
            elif target:
                cmd.extend(["-s", target])
                
            subprocess.Popen(cmd)
            return {"status": "success", "result": f"Launched scrcpy window for {online_device or target or 'default device'}"}
        except Exception as e:
            return {"status": "error", "result": str(e)}

    async def launch_app(self, app_name_or_pkg: str, serial: str = None) -> dict:
        """Launch an app on the Android device via ADB."""
        pkg_map = {
            "whatsapp": "com.whatsapp",
            "whatsapp business": "com.whatsapp.w4b",
            "youtube": "com.google.android.youtube",
            "chrome": "com.android.chrome",
            "instagram": "com.instagram.android",
            "spotify": "com.spotify.music",
            "settings": "com.android.settings",
            "camera": "com.android.camera",
            "gallery": "com.google.android.apps.photos",
            "maps": "com.google.android.apps.maps"
        }
        
        target_pkg = pkg_map.get(app_name_or_pkg.lower().strip(), app_name_or_pkg.strip())
        
        cmd_prefix = ["adb"]
        if serial:
            cmd_prefix.extend(["-s", serial])
            
        monkey_cmd = cmd_prefix + ["shell", "monkey", "-p", target_pkg, "-c", "android.intent.category.LAUNCHER", "1"]
        proc = await asyncio.create_subprocess_exec(
            *monkey_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out_str = stdout.decode() + stderr.decode()
        
        if "Events injected: 1" in out_str or proc.returncode == 0:
            return {"status": "success", "result": f"Opened {app_name_or_pkg} on device", "package": target_pkg}
            
        fallback_cmd = cmd_prefix + ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-n", f"{target_pkg}/.Main"]
        proc2 = await asyncio.create_subprocess_exec(
            *fallback_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout2, stderr2 = await proc2.communicate()
        return {
            "status": "success" if proc2.returncode == 0 else "error",
            "result": f"Launched {target_pkg}",
            "stdout": stdout2.decode(),
            "stderr": stderr2.decode()
        }

    async def control_input(self, action: str, text: str = "", x: int = 0, y: int = 0, serial: str = None) -> dict:
        """Control Android device inputs (keyevent, text typing, tap, swipe, unlock)."""
        cmd_prefix = ["adb"]
        if serial:
            cmd_prefix.extend(["-s", serial])
            
        if action == "text":
            safe_text = text.replace(" ", "%s")
            cmd = cmd_prefix + ["shell", "input", "text", safe_text]
        elif action == "tap":
            cmd = cmd_prefix + ["shell", "input", "tap", str(x), str(y)]
        elif action == "unlock":
            cmd1 = cmd_prefix + ["shell", "input", "keyevent", "224"]
            cmd2 = cmd_prefix + ["shell", "input", "keyevent", "82"]
            await (await asyncio.create_subprocess_exec(*cmd1)).communicate()
            await (await asyncio.create_subprocess_exec(*cmd2)).communicate()
            return {"status": "success", "result": "Unlocked device"}
        else:
            keyevents = {
                "power": "26", "back": "4", "home": "3",
                "vol_up": "24", "vol_down": "25", "enter": "66",
                "delete": "67", "app_switch": "187"
            }
            code = keyevents.get(action, action)
            cmd = cmd_prefix + ["shell", "input", "keyevent", code]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        }

adb_manager = ADBManager()
