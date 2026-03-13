"""
Luna YouTube Controller
- yt-dlp finds video ID (no download)
- Opens Firefox with &autoplay=1
- Waits 4s, checks if audio playing, presses K only if NOT playing
"""
import sys, shutil, time, threading, urllib.parse, subprocess
from core.env_helper import env, run as _re, popen as _pe

def _r(*cmd): return _re(*cmd, capture_output=True, text=True, timeout=25)

class YouTubeController:

    def search_and_play(self, query: str) -> tuple:
        vid, title = self._get_id(query)
        url  = (f"https://www.youtube.com/watch?v={vid}&autoplay=1"
                if vid else
                "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query))
        name = title or query
        if not self._open_firefox(url):
            return False, "Firefox not found. Install: sudo pacman -S firefox"
        threading.Thread(target=self._ensure_play, args=(bool(vid),), daemon=True).start()
        return True, f'Playing "{name}" on YouTube.'

    def _get_id(self, query: str) -> tuple:
        try:
            r = _r(sys.executable,"-m","yt_dlp","--no-playlist","--quiet","--no-warnings",
                   "--print","%(id)s\t%(title)s",f"ytsearch1:{query}")
            line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
            if "\t" in line:
                vid, title = line.split("\t",1); return vid.strip(), title.strip()
            r2 = _r(sys.executable,"-m","yt_dlp","--no-playlist","--quiet",
                    "--no-warnings","--get-id",f"ytsearch1:{query}")
            vid = r2.stdout.strip().splitlines()[0].strip() if r2.stdout.strip() else ""
            return vid, query
        except Exception: return "", ""

    def _open_firefox(self, url: str) -> bool:
        if not shutil.which("firefox"): return False
        already = subprocess.run(["pgrep","-x","firefox"],capture_output=True).returncode == 0
        _pe(*(["firefox","--new-tab",url] if already else ["firefox",url]),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True

    def _is_playing(self) -> bool:
        try:
            r = subprocess.run(["pactl","list","sink-inputs"],capture_output=True,text=True,env=env(),timeout=3)
            txt = r.stdout.lower()
            if "firefox" in txt and "corked: no" in txt: return True
            if 'application.name = "firefox"' in txt: return True
        except Exception: pass
        try:
            r = subprocess.run(["wpctl","status"],capture_output=True,text=True,env=env(),timeout=3)
            if "firefox" in r.stdout.lower(): return True
        except Exception: pass
        return False

    def _focus(self):
        try: subprocess.run(["hyprctl","dispatch","focuswindow","class:firefox"],
                            env=env(),capture_output=True,timeout=2)
        except Exception: pass

    def _key(self, k: str):
        for tool, args in [("ydotool",["ydotool","key",k]),
                           ("xdotool",["xdotool","key","--clearmodifiers",k])]:
            if shutil.which(tool):
                subprocess.run(args,env=env(),capture_output=True,timeout=2); return

    def _ensure_play(self, direct: bool):
        time.sleep(4.5 if direct else 6.0)
        self._focus(); time.sleep(0.5)
        if not direct:
            for _ in range(5): self._key("Tab"); time.sleep(0.12)
            self._key("Return"); time.sleep(5.0)
            self._focus(); time.sleep(0.4)
        if self._is_playing(): return   # already playing — do nothing
        self._key("k")                   # press K once
        time.sleep(1.5)
        if not self._is_playing(): self._key("space")  # last resort

    def pause_resume(self): self._focus(); time.sleep(0.2); self._key("k")
    def mute_video(self):   self._focus(); time.sleep(0.2); self._key("m")
    def fullscreen(self):   self._focus(); time.sleep(0.2); self._key("f")
