import React, { useState } from "react";
import { motion } from "motion/react";
import { Smartphone, X, Play, Power, ArrowLeft, Home, Volume2, VolumeX, MessageSquare, Youtube, Chrome, Settings, Camera, GripHorizontal, RefreshCw } from "lucide-react";

interface MobileScreenModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetDeviceSerial?: string;
  isLight?: boolean;
}

export default function MobileScreenModal({
  isOpen,
  onClose,
  targetDeviceSerial = "",
  isLight = false
}: MobileScreenModalProps) {
  const [statusText, setStatusText] = useState<string>("Ready");
  const [isMirroring, setIsMirroring] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleControl = async (action: string, text: string = "") => {
    try {
      setStatusText(`Sending ${action}...`);
      const response = await fetch("http://localhost:3000/api/agents/adb/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, target: targetDeviceSerial, text })
      });
      const data = await response.json();
      if (data.status === "success") {
        setStatusText(`Action executed: ${action}`);
      } else {
        setStatusText(`Failed: ${data.result || data.stderr}`);
      }
    } catch (e: any) {
      setStatusText(`Error: ${e.message}`);
    }
  };

  const handleLaunchApp = async (app: string) => {
    try {
      setStatusText(`Opening ${app}...`);
      const response = await fetch("http://localhost:3000/api/agents/adb/launch_app", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ app, target: targetDeviceSerial })
      });
      const data = await response.json();
      if (data.status === "success") {
        setStatusText(`Opened ${app} on phone`);
      } else {
        setStatusText(`Failed to open ${app}`);
      }
    } catch (e: any) {
      setStatusText(`Error: ${e.message}`);
    }
  };

  const handleLaunchScrcpy = async () => {
    setIsMirroring(true);
    setStatusText("Launching desktop mirror (scrcpy)...");
    try {
      const response = await fetch("http://localhost:3000/api/agents/adb/scrcpy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: targetDeviceSerial })
      });
      const data = await response.json();
      if (data.status === "success") {
        setStatusText(data.result);
      } else {
        setStatusText(`Scrcpy error: ${data.result}`);
      }
    } catch (e: any) {
      setStatusText(`Error: ${e.message}`);
    } finally {
      setTimeout(() => setIsMirroring(false), 2000);
    }
  };

  return (
    <motion.div
      drag
      dragMomentum={false}
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="fixed z-50 top-16 right-12 w-[340px] rounded-3xl overflow-hidden shadow-2xl border backdrop-blur-xl bg-slate-950/90 border-cyan-500/40 text-white select-none"
    >
      {/* Top Window Drag Header */}
      <div className="bg-slate-900/90 px-4 py-3 border-b border-slate-800 flex items-center justify-between cursor-grab active:cursor-grabbing">
        <div className="flex items-center gap-2">
          <GripHorizontal className="w-4 h-4 text-slate-500" />
          <div className="flex items-center gap-1.5">
            <Smartphone className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold font-mono tracking-wider text-slate-200">
              MOBILE REMOTE SCREEN
            </span>
          </div>
        </div>

        {/* Close Button on Top of Screen */}
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-full bg-slate-800 hover:bg-rose-600 text-slate-300 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          title="Close Mobile Screen Window"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Main Body */}
      <div className="p-4 space-y-4">
        {/* Status Bar */}
        <div className="flex items-center justify-between text-[10px] font-mono px-2 py-1 bg-slate-900/60 rounded-lg border border-slate-800">
          <span className="text-cyan-400 truncate max-w-[200px]">
            {statusText}
          </span>
          <span className="flex items-center gap-1 text-emerald-400 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            ONLINE
          </span>
        </div>

        {/* Floating Mobile Phone Frame */}
        <div className="relative w-full h-[400px] rounded-2xl border-2 border-slate-700 bg-slate-900 overflow-hidden flex flex-col justify-between shadow-inner">
          {/* Top Speaker Notch */}
          <div className="w-full py-1.5 bg-black/80 flex justify-center items-center gap-2 z-10 border-b border-slate-800">
            <div className="w-12 h-1 bg-slate-700 rounded-full" />
            <div className="w-2 h-2 bg-slate-800 rounded-full" />
          </div>

          {/* Phone Display Content */}
          <div className="flex-1 p-3 flex flex-col justify-between relative bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900">
            {/* Quick App Dock */}
            <div>
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest block mb-2 text-center">
                Quick App Launcher
              </span>
              <div className="grid grid-cols-5 gap-2">
                <button
                  onClick={() => handleLaunchApp("whatsapp")}
                  className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 hover:bg-emerald-900/50 text-emerald-400 flex flex-col items-center gap-1 transition-all cursor-pointer"
                  title="Open WhatsApp"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="text-[8px] font-mono">WhatsApp</span>
                </button>

                <button
                  onClick={() => handleLaunchApp("youtube")}
                  className="p-2.5 rounded-xl bg-rose-950/40 border border-rose-500/30 hover:bg-rose-900/50 text-rose-400 flex flex-col items-center gap-1 transition-all cursor-pointer"
                  title="Open YouTube"
                >
                  <Youtube className="w-4 h-4" />
                  <span className="text-[8px] font-mono">YouTube</span>
                </button>

                <button
                  onClick={() => handleLaunchApp("chrome")}
                  className="p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/30 hover:bg-amber-900/50 text-amber-400 flex flex-col items-center gap-1 transition-all cursor-pointer"
                  title="Open Chrome"
                >
                  <Chrome className="w-4 h-4" />
                  <span className="text-[8px] font-mono">Chrome</span>
                </button>

                <button
                  onClick={() => handleLaunchApp("camera")}
                  className="p-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 hover:bg-purple-900/50 text-purple-400 flex flex-col items-center gap-1 transition-all cursor-pointer"
                  title="Open Camera"
                >
                  <Camera className="w-4 h-4" />
                  <span className="text-[8px] font-mono">Camera</span>
                </button>

                <button
                  onClick={() => handleLaunchApp("settings")}
                  className="p-2.5 rounded-xl bg-cyan-950/40 border border-cyan-500/30 hover:bg-cyan-900/50 text-cyan-400 flex flex-col items-center gap-1 transition-all cursor-pointer"
                  title="Open Settings"
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-[8px] font-mono">Settings</span>
                </button>
              </div>
            </div>

            {/* Desktop Scrcpy Mirror Action Banner */}
            <div className="my-auto text-center p-3 rounded-xl border border-cyan-500/20 bg-cyan-950/20 backdrop-blur-sm space-y-2">
              <span className="text-[10px] font-mono text-cyan-400 block font-bold">
                SCRCPY SCREEN MIRRORING
              </span>
              <p className="text-[9px] text-slate-400">
                Launch full 60fps interactive phone window on your Linux desktop.
              </p>
              <button
                onClick={handleLaunchScrcpy}
                disabled={isMirroring}
                className="w-full py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold font-mono text-xs rounded-lg flex items-center justify-center gap-1.5 transition-all shadow-md cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-slate-950" />
                {isMirroring ? "LAUNCHING..." : "LAUNCH DESKTOP MIRROR"}
              </button>
            </div>

            {/* Phone Bottom Navigation Bar */}
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-around">
              <button
                onClick={() => handleControl("back")}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer"
                title="Back Button"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>

              <button
                onClick={() => handleControl("home")}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer"
                title="Home Button"
              >
                <Home className="w-4 h-4 text-cyan-400" />
              </button>

              <button
                onClick={() => handleControl("power")}
                className="p-2 rounded-lg hover:bg-slate-800 text-rose-400 hover:text-rose-300 transition-colors cursor-pointer"
                title="Power Button"
              >
                <Power className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Volume & Hardware Quick Controls */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleControl("vol_up")}
            className="py-2 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs font-mono text-emerald-400 flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Volume2 className="w-3.5 h-3.5" /> VOL UP
          </button>
          <button
            onClick={() => handleControl("vol_down")}
            className="py-2 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs font-mono text-slate-400 flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <VolumeX className="w-3.5 h-3.5" /> VOL DOWN
          </button>
        </div>
      </div>
    </motion.div>
  );
}
