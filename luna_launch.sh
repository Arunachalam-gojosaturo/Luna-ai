#!/usr/bin/env bash
cd "/home/arunachalam/Downloads/Luna-ai"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
export DISPLAY="${DISPLAY:-:0}"
export MOZ_ENABLE_WAYLAND=1
export QT_QPA_PLATFORM=wayland
[ -f "/home/arunachalam/Downloads/Luna-ai/venv/bin/activate" ]  && source "/home/arunachalam/Downloads/Luna-ai/venv/bin/activate"
[ -f "/home/arunachalam/Downloads/Luna-ai/.venv/bin/activate" ] && source "/home/arunachalam/Downloads/Luna-ai/.venv/bin/activate"
exec python "/home/arunachalam/Downloads/Luna-ai/main.py" "$@"
