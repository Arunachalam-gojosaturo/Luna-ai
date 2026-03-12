import re, subprocess, shutil, glob


def _r(*cmd):
    return subprocess.run(list(cmd), capture_output=True, text=True)


class BrightnessCtrl:
    @staticmethod
    def available():
        return bool(shutil.which("brightnessctl"))

    def get(self) -> int:
        # Try brightnessctl
        try:
            cur = int(_r("brightnessctl","get").stdout.strip())
            mx  = int(_r("brightnessctl","max").stdout.strip())
            return round(cur/mx*100) if mx else 0
        except Exception:
            pass
        # Fallback: sysfs
        for d in glob.glob("/sys/class/backlight/*/"):
            try:
                cur = int(open(d+"brightness").read())
                mx  = int(open(d+"max_brightness").read())
                return round(cur/mx*100)
            except Exception:
                pass
        return -1

    def _bcset(self, *args) -> bool:
        for prefix in [["brightnessctl"], ["sudo","-n","brightnessctl"]]:
            r = subprocess.run(prefix+list(args), capture_output=True, text=True)
            if r.returncode == 0:
                return True
        # Last resort: write directly to sysfs
        for d in glob.glob("/sys/class/backlight/*/"):
            try:
                mx = int(open(d+"max_brightness").read())
                # Parse the arg to get value
                arg = args[-1] if args else "50%"
                pct = int(arg.replace("%","").replace("+","").replace("-",""))
                newval = int(mx * pct / 100)
                with open(d+"brightness","w") as f:
                    f.write(str(newval))
                return True
            except Exception:
                pass
        return False

    def set_pct(self, pct:int):
        pct = max(1,min(100,pct))
        ok = self._bcset("set",f"{pct}%")
        cur = self.get()
        return ok, f"Brightness {'set to '+str(pct)+'%' if ok else 'failed. Run: sudo usermod -aG video $USER then re-login'}." + (f" Current: {cur}%" if ok else "")

    def up(self, step=10):
        ok = self._bcset("set",f"+{step}%")
        cur = self.get()
        return ok, f"Brightness up to {cur}%."

    def down(self, step=10):
        ok = self._bcset("set",f"{step}%-")
        cur = self.get()
        return ok, f"Brightness down to {cur}%."

    def max_b(self):
        ok = self._bcset("set","100%")
        return ok, "Brightness at max."

    def min_b(self):
        ok = self._bcset("set","5%")
        return ok, "Brightness at minimum."


class VolumeCtrl:
    SINK = "@DEFAULT_AUDIO_SINK@"
    SRC  = "@DEFAULT_AUDIO_SOURCE@"

    @staticmethod
    def available():
        return any(shutil.which(t) for t in ["wpctl","pactl","amixer"])

    def get(self) -> int:
        try:
            r = _r("wpctl","get-volume","@DEFAULT_AUDIO_SINK@")
            m = re.search(r"Volume:\s*([\d.]+)", r.stdout)
            if m: return int(float(m.group(1))*100)
        except Exception: pass
        try:
            r = _r("pactl","get-sink-volume","@DEFAULT_SINK@")
            m = re.search(r"(\d+)%", r.stdout)
            if m: return int(m.group(1))
        except Exception: pass
        return -1

    def is_muted(self):
        try: return "MUTED" in _r("wpctl","get-volume","@DEFAULT_AUDIO_SINK@").stdout
        except Exception: return False

    def _do(self, *wp_args):
        r = _r("wpctl", *wp_args)
        if r.returncode == 0: return True
        # pactl fallback mapping
        mapping = {
            ("set-volume", self.SINK): lambda v: _r("pactl","set-sink-volume","@DEFAULT_SINK@",v),
            ("set-mute",   self.SINK): lambda v: _r("pactl","set-sink-mute","@DEFAULT_SINK@",v),
        }
        return r.returncode == 0

    def set_pct(self, pct:int):
        pct = max(0,min(150,pct))
        fval = f"{pct/100:.2f}"
        r = _r("wpctl","set-volume",self.SINK,fval)
        if r.returncode != 0:
            _r("pactl","set-sink-volume","@DEFAULT_SINK@",f"{pct}%")
        cur = self.get()
        return True, f"Volume set to {pct}%. Current: {cur}%."

    def up(self, step=10):
        r = _r("wpctl","set-volume","-l","1.5",self.SINK,f"{step}%+")
        if r.returncode != 0:
            _r("pactl","set-sink-volume","@DEFAULT_SINK@",f"+{step}%")
        cur = self.get()
        return True, f"Volume up to {cur}%."

    def down(self, step=10):
        r = _r("wpctl","set-volume",self.SINK,f"{step}%-")
        if r.returncode != 0:
            _r("pactl","set-sink-volume","@DEFAULT_SINK@",f"-{step}%")
        cur = self.get()
        return True, f"Volume down to {cur}%."

    def mute(self):
        r = _r("wpctl","set-mute",self.SINK,"1")
        if r.returncode != 0: _r("pactl","set-sink-mute","@DEFAULT_SINK@","1")
        return True, "Muted."

    def unmute(self):
        r = _r("wpctl","set-mute",self.SINK,"0")
        if r.returncode != 0: _r("pactl","set-sink-mute","@DEFAULT_SINK@","0")
        return True, "Unmuted."

    def mic_mute(self):
        r = _r("wpctl","set-mute",self.SRC,"1")
        return (True,"Mic muted.") if r.returncode==0 else (False,"Mic mute failed.")

    def mic_unmute(self):
        r = _r("wpctl","set-mute",self.SRC,"0")
        return (True,"Mic unmuted.") if r.returncode==0 else (False,"Mic unmute failed.")
