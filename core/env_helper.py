"""
Luna Environment Helper — fixes subprocess env when launched as desktop app.
Wayland/DBus/PATH vars are missing in desktop launches; this injects them.
"""
import os, subprocess
from pathlib import Path

_ENV_CACHE = None

def env() -> dict:
    global _ENV_CACHE
    if _ENV_CACHE:
        return _ENV_CACHE
    e   = dict(os.environ)
    uid = os.getuid()
    # Wayland socket
    if not e.get("WAYLAND_DISPLAY"):
        for c in ["wayland-1","wayland-0"]:
            if Path(f"/run/user/{uid}/{c}").exists():
                e["WAYLAND_DISPLAY"] = c; break
        else:
            e["WAYLAND_DISPLAY"] = "wayland-1"
    e.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    if not e.get("DBUS_SESSION_BUS_ADDRESS"):
        bus = f"/run/user/{uid}/bus"
        if Path(bus).exists():
            e["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"
    e.setdefault("DISPLAY", ":0")
    e.setdefault("XDG_SESSION_TYPE", "wayland")
    e.setdefault("MOZ_ENABLE_WAYLAND", "1")
    e.setdefault("HOME", str(Path.home()))
    # Ensure /usr/bin in PATH
    parts = e.get("PATH","").split(":")
    for p in ["/usr/bin","/usr/local/bin","/bin",f"{Path.home()}/.local/bin"]:
        if p not in parts: parts.insert(0, p)
    e["PATH"] = ":".join(x for x in parts if x)
    _ENV_CACHE = e
    return e

def run(*args, **kw) -> subprocess.CompletedProcess:
    kw.setdefault("env", env())
    return subprocess.run(list(args), **kw)

def popen(*args, **kw) -> subprocess.Popen:
    kw.setdefault("env", env())
    return subprocess.Popen(list(args), **kw)
