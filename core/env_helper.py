"""
Luna Environment Helper — injects Wayland/DBus/PATH into subprocesses.
Sets TMPDIR=/tmp which fixes pip OSError on Python 3.14.
"""
import os, subprocess
from pathlib import Path

_CACHE = None

def env() -> dict:
    global _CACHE
    if _CACHE:
        return _CACHE
    e   = dict(os.environ)
    uid = os.getuid()
    e.setdefault("TMPDIR", "/tmp")
    if not e.get("WAYLAND_DISPLAY"):
        for c in ["wayland-1", "wayland-0"]:
            if Path(f"/run/user/{uid}/{c}").exists():
                e["WAYLAND_DISPLAY"] = c; break
        else:
            e.setdefault("WAYLAND_DISPLAY", "wayland-1")
    e.setdefault("XDG_RUNTIME_DIR",    f"/run/user/{uid}")
    e.setdefault("DISPLAY",            ":0")
    e.setdefault("XDG_SESSION_TYPE",   "wayland")
    e.setdefault("MOZ_ENABLE_WAYLAND", "1")
    e.setdefault("HOME",               str(Path.home()))
    if not e.get("DBUS_SESSION_BUS_ADDRESS"):
        bus = f"/run/user/{uid}/bus"
        if Path(bus).exists():
            e["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"
    parts = e.get("PATH", "").split(":")
    for p in ["/usr/bin", "/usr/local/bin", "/bin", f"{Path.home()}/.local/bin"]:
        if p not in parts: parts.insert(0, p)
    e["PATH"] = ":".join(x for x in parts if x)
    _CACHE = e
    return e

def run(*args, **kw):
    kw.setdefault("env", env())
    return subprocess.run(list(args), **kw)

def popen(*args, **kw):
    kw.setdefault("env", env())
    return subprocess.Popen(list(args), **kw)
