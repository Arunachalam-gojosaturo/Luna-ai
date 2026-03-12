"""Open YouTube video in Firefox by searching via yt-dlp (no download)."""
import subprocess, shutil, sys, time, urllib.parse


class YouTubeController:

    def search_and_play(self, query:str) -> tuple[bool,str]:
        vid, title = self._get_id(query)
        if vid:
            url  = f"https://www.youtube.com/watch?v={vid}"
            name = title or query
        else:
            url  = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
            name = query
        ok = self._open(url)
        if not ok:
            return False, "Firefox not found. Install: sudo pacman -S firefox"
        return True, f'Opened "{name}" on YouTube in Firefox.'

    def _get_id(self, query:str) -> tuple[str,str]:
        """yt-dlp metadata only — no audio/video download at all."""
        try:
            r = subprocess.run(
                [sys.executable,"-m","yt_dlp",
                 "--no-playlist","--quiet","--no-warnings",
                 "--print","%(id)s\t%(title)s",
                 f"ytsearch1:{query}"],
                capture_output=True, text=True, timeout=20)
            line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
            if "\t" in line:
                vid, title = line.split("\t", 1)
                return vid.strip(), title.strip()
            # fallback: old --get-id style
            r2 = subprocess.run(
                [sys.executable,"-m","yt_dlp",
                 "--no-playlist","--quiet","--no-warnings",
                 "--get-id", f"ytsearch1:{query}"],
                capture_output=True, text=True, timeout=20)
            vid = r2.stdout.strip().splitlines()[0].strip() if r2.stdout.strip() else ""
            return vid, query
        except Exception:
            return "", ""

    def _open(self, url:str) -> bool:
        if not shutil.which("firefox"):
            return False
        already = subprocess.run(["pgrep","-x","firefox"],
                                  capture_output=True).returncode == 0
        cmd = ["firefox","--new-tab",url] if already else ["firefox",url]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return True

    def _focus(self):
        for cmd in [["hyprctl","dispatch","focuswindow","class:firefox"],
                    ["wmctrl","-a","Firefox"]]:
            try: subprocess.run(cmd, capture_output=True, timeout=2); break
            except Exception: pass
        time.sleep(0.3)

    def _key(self, k:str):
        for tool,args in [("ydotool",["ydotool","key",k]),
                          ("xdotool",["xdotool","key","--clearmodifiers",k])]:
            if shutil.which(tool):
                subprocess.run(args, capture_output=True, timeout=2); return

    def pause_resume(self): self._focus(); self._key("k")
    def mute_video(self):   self._focus(); self._key("m")
    def fullscreen(self):   self._focus(); self._key("f")
