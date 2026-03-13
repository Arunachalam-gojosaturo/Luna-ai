"""Luna System Controller — Brightness (brightnessctl) + Volume (wpctl/pactl)."""
import re, shutil, glob, subprocess
from core.env_helper import env

def _r(*cmd):
    return subprocess.run(list(cmd), capture_output=True, text=True, env=env())

class BrightnessCtrl:
    @staticmethod
    def available(): return bool(shutil.which("brightnessctl"))

    def get(self) -> int:
        try:
            cur = int(_r("brightnessctl","get").stdout.strip())
            mx  = int(_r("brightnessctl","max").stdout.strip())
            return round(cur/mx*100) if mx else 0
        except Exception:
            for d in glob.glob("/sys/class/backlight/*/"):
                try:
                    cur = int(open(d+"brightness").read())
                    mx  = int(open(d+"max_brightness").read())
                    return round(cur/mx*100)
                except Exception: pass
        return -1

    def _set(self, *args) -> bool:
        for prefix in [["brightnessctl"], ["sudo","-n","brightnessctl"]]:
            if subprocess.run(prefix+list(args), capture_output=True,
                              text=True, env=env()).returncode == 0:
                return True
        # sysfs direct write
        for d in glob.glob("/sys/class/backlight/*/"):
            try:
                mx = int(open(d+"max_brightness").read())
                raw = str(args[-1]).replace("%","").replace("+","").replace("-","")
                val = int(mx * int(raw) / 100)
                open(d+"brightness","w").write(str(max(1,min(mx,val))))
                return True
            except Exception: pass
        return False

    def set_pct(self, pct):
        pct = max(1,min(100,pct)); ok = self._set("set",f"{pct}%"); c = self.get()
        return ok, (f"Brightness set to {pct}%. Current: {c}%." if ok else
                    "Brightness failed. Run: sudo usermod -aG video $USER then re-login.")
    def up(self, step=10):
        ok = self._set("set",f"+{step}%"); c = self.get()
        return ok, f"Brightness increased to {c}%."
    def down(self, step=10):
        ok = self._set("set",f"{step}%-"); c = self.get()
        return ok, f"Brightness decreased to {c}%."
    def max_b(self):
        ok = self._set("set","100%"); return ok, "Brightness at maximum."
    def min_b(self):
        ok = self._set("set","5%");  return ok, "Brightness at minimum."


class VolumeCtrl:
    SINK = "@DEFAULT_AUDIO_SINK@"
    SRC  = "@DEFAULT_AUDIO_SOURCE@"
    @staticmethod
    def available(): return any(shutil.which(t) for t in ["wpctl","pactl","amixer"])

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

    def is_muted(self) -> bool:
        try: return "MUTED" in _r("wpctl","get-volume","@DEFAULT_AUDIO_SINK@").stdout
        except Exception: return False

    def _wp(self,*a): return _r("wpctl",*a)
    def _pa(self,*a): return _r("pactl",*a)

    def set_pct(self, pct):
        pct = max(0,min(150,pct))
        r = self._wp("set-volume",self.SINK,f"{pct/100:.2f}")
        if r.returncode != 0: self._pa("set-sink-volume","@DEFAULT_SINK@",f"{pct}%")
        return True, f"Volume set to {pct}%. Current: {self.get()}%."
    def up(self, step=10):
        r = self._wp("set-volume","-l","1.5",self.SINK,f"{step}%+")
        if r.returncode != 0: self._pa("set-sink-volume","@DEFAULT_SINK@",f"+{step}%")
        return True, f"Volume up to {self.get()}%."
    def down(self, step=10):
        r = self._wp("set-volume",self.SINK,f"{step}%-")
        if r.returncode != 0: self._pa("set-sink-volume","@DEFAULT_SINK@",f"-{step}%")
        return True, f"Volume down to {self.get()}%."
    def mute(self):
        r = self._wp("set-mute",self.SINK,"1")
        if r.returncode != 0: self._pa("set-sink-mute","@DEFAULT_SINK@","1")
        return True, "Volume muted."
    def unmute(self):
        r = self._wp("set-mute",self.SINK,"0")
        if r.returncode != 0: self._pa("set-sink-mute","@DEFAULT_SINK@","0")
        return True, "Volume unmuted."
    def mic_mute(self):
        r = self._wp("set-mute",self.SRC,"1")
        return (True,"Mic muted.") if r.returncode==0 else (False,"Mic mute failed.")
    def mic_unmute(self):
        r = self._wp("set-mute",self.SRC,"0")
        return (True,"Mic unmuted.") if r.returncode==0 else (False,"Mic unmute failed.")
