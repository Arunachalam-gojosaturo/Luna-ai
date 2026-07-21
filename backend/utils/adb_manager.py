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
    - Automatically enables TCP/IP mode and connects via Wireless ADB
    - Saves & remembers devices persistently in saved_adb_devices.json
    - Automatically reconnects saved wireless devices when disconnected
    - Provides high-level mobile controls (WhatsApp, apps, keyevents, tap, text)
    """

    def __init__(self):
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
            print(f"[ADBManager] Saved device '{key}': {info}")
        except Exception as e:
            print(f"[ADBManager] Failed to save device info: {e}")

    async def get_device_ip(self, serial: str) -> Optional[str]:
        """Attempt multiple methods to retrieve the Wi-Fi IP of an Android device over USB."""
        commands = [
            ["adb", "-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0"],
            ["adb", "-s", serial, "shell", "ip", "route"],
            ["adb", "-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress"],
            ["adb", "-s", serial, "shell", "ifconfig", "wlan0"]
        ]
        
        for cmd in commands:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                out = stdout.decode().strip()
                
                # Look for IPv4 addresses (excluding 127.0.0.1)
                matches = re.findall(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b", out)
                if matches:
                    return matches[0]
                
                # Generic IPv4 fallback if on custom subnet
                matches_gen = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", out)
                for ip in matches_gen:
                    if not ip.startswith("127.") and not ip.startswith("0.") and not ip.endswith(".255"):
                        return ip
            except Exception:
                continue
        return None

    async def scan_and_auto_connect(self) -> List[dict]:
        """
        Scan devices, detect USB phone IPs, configure Wireless TCP/IP, 
        auto-reconnect saved wireless devices, and return active device list.
        """
        # 1. First attempt to reconnect all saved wireless devices
        saved = self.load_saved_devices()
        for device_key, info in saved.items():
            ip = info.get("ip")
            port = info.get("port", "5555")
            if ip:
                target = f"{ip}:{port}"
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "adb", "connect", target,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await proc.communicate()
                except Exception:
                    pass

        # 2. Get current adb devices list
        devices = []
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "devices", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            lines = stdout.decode().strip().split("\n")
            
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

                        is_wireless = ":" in serial

                        device_entry = {
                            "serial": serial,
                            "status": status,
                            "model": model,
                            "is_wireless": is_wireless
                        }
                        devices.append(device_entry)

                        # 3. If USB connected, auto-discover Wireless IP & enable tcpip
                        if not is_wireless and status == "device":
                            ip = await self.get_device_ip(serial)
                            if ip:
                                device_entry["ip"] = ip
                                self.save_device_info(serial, {
                                    "serial": serial,
                                    "model": model,
                                    "ip": ip,
                                    "port": "5555"
                                })
                                # Enable TCP/IP on port 5555
                                tcp_proc = await asyncio.create_subprocess_exec(
                                    "adb", "-s", serial, "tcpip", "5555",
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE
                                )
                                await tcp_proc.communicate()
                                # Try connecting wirelessly
                                conn_proc = await asyncio.create_subprocess_exec(
                                    "adb", "connect", f"{ip}:5555",
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE
                                )
                                await conn_proc.communicate()

        except Exception as e:
            print(f"[ADBManager] Error scanning ADB devices: {e}")

        return devices

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
        
        # Determine target device
        cmd_prefix = ["adb"]
        if serial:
            cmd_prefix.extend(["-s", serial])
            
        # First try monkey launcher
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
            
        # Fallback to am start
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
            # Escape spaces for adb input text
            safe_text = text.replace(" ", "%s")
            cmd = cmd_prefix + ["shell", "input", "text", safe_text]
        elif action == "tap":
            cmd = cmd_prefix + ["shell", "input", "tap", str(x), str(y)]
        elif action == "unlock":
            # Wake up and swipe to unlock
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
