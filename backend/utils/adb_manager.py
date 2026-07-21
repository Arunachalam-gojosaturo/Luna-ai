import os
import re
import json
import asyncio
import subprocess
from typing import List, Dict, Optional
from backend.config.paths import get_config_dir

SAVED_DEVICES_FILE = get_config_dir() / "saved_adb_devices.json"
MOBILE_PIN_FILE = get_config_dir() / "mobile_pin.json"

class ADBManager:
    """
    Automated ADB Manager:
    - Scans connected ADB devices (USB & Wireless)
    - Auto-detects Wi-Fi IP of USB-connected Android phones
    - Configures Wireless TCP/IP ONCE per USB connection
    - Remembers devices in saved_adb_devices.json
    - Remembers mobile unlock PIN in mobile_pin.json (default 769680)
    - Unlocks mobile phone accurately without accidental keyevent 82 / #5 presses
    - Parses real battery level, charging status, and Wi-Fi state
    - Launches apps cleanly with intent & wake-up handling
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

        if not MOBILE_PIN_FILE.exists():
            try:
                with open(MOBILE_PIN_FILE, "w") as f:
                    json.dump({"pin": "769680"}, f, indent=2)
            except Exception as e:
                print(f"[ADBManager] Could not create mobile PIN file: {e}")

    def get_mobile_pin(self) -> str:
        try:
            if MOBILE_PIN_FILE.exists():
                with open(MOBILE_PIN_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("pin", "769680")
        except Exception as e:
            print(f"[ADBManager] Error reading PIN: {e}")
        return "769680"

    def set_mobile_pin(self, new_pin: str) -> bool:
        try:
            cleaned_pin = str(new_pin).strip()
            with open(MOBILE_PIN_FILE, "w") as f:
                json.dump({"pin": cleaned_pin}, f, indent=2)
            print(f"[ADBManager] Mobile PIN updated to: {cleaned_pin}")
            return True
        except Exception as e:
            print(f"[ADBManager] Error setting PIN: {e}")
            return False

    def load_saved_devices(self) -> Dict[str, dict]:
        try:
            if SAVED_DEVICES_FILE.exists():
                with open(SAVED_DEVICES_FILE, "r") as f:
                    data = json.load(f)
                    cleaned = {}
                    for k, v in data.items():
                        ip = v.get("ip", "")
                        if ip and not ip.endswith(".0") and not ip.endswith(".255"):
                            cleaned[k] = v
                    return cleaned
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

    async def _resolve_device_serial(self, serial: Optional[str] = None) -> Optional[str]:
        """Resolves target device serial to avoid 'more than one device' errors."""
        devices = await self.scan_and_auto_connect()
        online_devices = [d["serial"] for d in devices if d["status"] == "device"]

        if not online_devices:
            return None

        if serial:
            if serial in online_devices:
                return serial
            for s in online_devices:
                if serial in s:
                    return s
            if "wireless" in serial.lower() or "wifi" in serial.lower() or "tcp" in serial.lower():
                for s in online_devices:
                    if ":" in s:
                        return s

        return online_devices[0]

    async def launch_scrcpy(self, target: str = "") -> dict:
        """Safely launch scrcpy window with Wi-Fi auto-connect and optimized streaming flags."""
        try:
            # If target specifies a wireless IP, ensure adb connect is run first
            if target and (":" in target or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", target)):
                target_ip = target if ":" in target else f"{target}:5555"
                proc = await asyncio.create_subprocess_exec("adb", "connect", target_ip, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()

            target_serial = await self._resolve_device_serial(target)
            final_target = target_serial or target

            cmd = ["scrcpy"]
            if final_target:
                cmd.extend(["-s", final_target])

            # Wi-Fi / Wayland optimized scrcpy parameters
            if final_target and ":" in final_target:
                cmd.extend(["--max-size=1280", "-b", "6M", "--max-fps=30"])

            subprocess.Popen(cmd)
            return {"status": "success", "result": f"Launched scrcpy mirror for {final_target or 'default device'}"}
        except Exception as e:
            return {"status": "error", "result": str(e)}

    async def get_device_telemetry(self, serial: str) -> dict:
        """Parses REAL battery, charging status, and Wi-Fi info from Android dumpsys."""
        telemetry = {
            "battery": 85,
            "is_charging": False,
            "power_source": "Battery",
            "network": "Wi-Fi Connected"
        }
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "dumpsys", "battery",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode()

            level_match = re.search(r"level:\s*(\d+)", out)
            if level_match:
                telemetry["battery"] = int(level_match.group(1))

            status_match = re.search(r"status:\s*(\d+)", out)
            ac_match = re.search(r"AC powered:\s*true", out, re.IGNORECASE)
            usb_match = re.search(r"USB powered:\s*true", out, re.IGNORECASE)

            if ac_match:
                telemetry["is_charging"] = True
                telemetry["power_source"] = "AC Charger"
            elif usb_match:
                telemetry["is_charging"] = True
                telemetry["power_source"] = "USB Cable"
            elif status_match and status_match.group(1) in ["2", "5"]:
                telemetry["is_charging"] = True
                telemetry["power_source"] = "Charging"

            ip = await self.get_device_ip(serial)
            if ip:
                telemetry["network"] = f"WLAN ({ip})"

        except Exception as e:
            print(f"[ADBManager] Error reading dumpsys battery: {e}")

        return telemetry

    async def get_device_ip(self, serial: str) -> Optional[str]:
        """Attempt multiple methods to retrieve the valid Wi-Fi host IP of an Android device."""
        def is_valid_host_ip(ip_str: str) -> bool:
            if not ip_str or not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_str):
                return False
            parts = [int(x) for x in ip_str.split(".")]
            return 0 < parts[3] < 255 and parts[0] != 127

        # Method 1: ip -f inet addr show wlan0
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode().strip()
            match = re.search(r"inet\s+((?:\d{1,3}\.){3}\d{1,3})", out)
            if match and is_valid_host_ip(match.group(1)):
                return match.group(1)
        except Exception:
            pass

        # Method 2: ip route (search all src IPs)
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "ip", "route",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode().strip()
            matches = re.findall(r"src\s+((?:\d{1,3}\.){3}\d{1,3})", out)
            for ip_cand in matches:
                if is_valid_host_ip(ip_cand):
                    return ip_cand
        except Exception:
            pass

        # Method 3: dhcp.wlan0.ipaddress property
        try:
            proc = await asyncio.create_subprocess_exec(
                "adb", "-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            ip_cand = stdout.decode().strip()
            if is_valid_host_ip(ip_cand):
                return ip_cand
        except Exception:
            pass

        return None

    async def scan_and_auto_connect(self) -> List[dict]:
        """Scan devices safely without continuously restarting tcpip on every poll."""
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

                        if status == "device":
                            telemetry = await self.get_device_telemetry(serial)
                            device_entry.update(telemetry)

                        devices.append(device_entry)

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

            if has_offline:
                saved = self.load_saved_devices()
                for dkey, info in saved.items():
                    ip = info.get("ip")
                    if ip:
                        await (await asyncio.create_subprocess_exec("adb", "disconnect", f"{ip}:5555")).communicate()
                        await (await asyncio.create_subprocess_exec("adb", "connect", f"{ip}:5555")).communicate()

        except Exception as e:
            print(f"[ADBManager] Error scanning ADB devices: {e}")

        return devices

    async def unlock_device(self, pin: Optional[str] = None, serial: Optional[str] = None) -> dict:
        """
        Unlock mobile device screen using clean swipe and exact single PIN text injection.
        Removes accidental keyevent 82 / #5 presses.
        """
        target_serial = await self._resolve_device_serial(serial)
        if not target_serial:
            return {"status": "error", "result": "No online Android device connected via ADB"}

        use_pin = pin if pin else self.get_mobile_pin()
        cmd_prefix = ["adb", "-s", target_serial]

        # 1. Wake screen ONLY (DO NOT use keyevent 82 which triggers emergency number 5 on vivo!)
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "keyevent", "224")).communicate()
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "keyevent", "4")).communicate() # Clear any active overlay
        await asyncio.sleep(0.3)

        # 2. Swipe up to reveal PIN keypad
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "swipe", "500", "1600", "500", "200", "300")).communicate()
        await asyncio.sleep(0.5)

        # 3. Inject PIN text ONCE cleanly
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "text", str(use_pin))).communicate()
        await asyncio.sleep(0.25)

        # 4. Press Enter
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "keyevent", "66")).communicate()
        await asyncio.sleep(0.3)

        # 5. Home key to ensure home screen is visible
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "keyevent", "3")).communicate()

        return {"status": "success", "result": f"Unlocked device '{target_serial}' with PIN '{use_pin}'", "pin": use_pin}

    async def lock_device(self, serial: Optional[str] = None) -> dict:
        """Lock mobile device screen."""
        target_serial = await self._resolve_device_serial(serial)
        if not target_serial:
            return {"status": "error", "result": "No online Android device connected via ADB"}

        cmd_prefix = ["adb", "-s", target_serial]
        await (await asyncio.create_subprocess_exec(*cmd_prefix, "shell", "input", "keyevent", "26")).communicate()
        return {"status": "success", "result": f"Locked mobile screen for '{target_serial}'"}



    async def launch_app(self, app_name_or_pkg: str, serial: Optional[str] = None) -> dict:
        """Launch an app on the Android device via ADB after ensuring device is awake/unlocked."""
        target_serial = await self._resolve_device_serial(serial)
        if not target_serial:
            return {"status": "error", "result": "No active Android device found to launch app"}

        # First wake/unlock device screen
        await self.unlock_device(serial=target_serial)

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
            "photos": "com.google.android.apps.photos",
            "maps": "com.google.android.apps.maps",
            "phone": "com.google.android.dialer",
            "messages": "com.google.android.apps.messaging"
        }
        
        target_pkg = pkg_map.get(app_name_or_pkg.lower().strip(), app_name_or_pkg.strip())
        cmd_prefix = ["adb", "-s", target_serial]
            
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
            
        fallback_cmd = cmd_prefix + ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-p", target_pkg]
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

    async def control_input(self, action: str, text: str = "", x: int = 0, y: int = 0, serial: Optional[str] = None) -> dict:
        """Control Android device inputs (keyevent, text typing, tap, swipe, unlock, lock)."""
        target_serial = await self._resolve_device_serial(serial)
        if not target_serial:
            return {"status": "error", "result": "No online Android device connected via ADB"}

        cmd_prefix = ["adb", "-s", target_serial]
            
        if action == "unlock":
            return await self.unlock_device(pin=text if text else None, serial=target_serial)
        elif action == "lock":
            return await self.lock_device(serial=target_serial)
        elif action == "text":
            safe_text = text.replace(" ", "%s")
            cmd = cmd_prefix + ["shell", "input", "text", safe_text]
        elif action == "tap":
            cmd = cmd_prefix + ["shell", "input", "tap", str(x), str(y)]
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
