import React from 'react';
import { TTSSettings } from '../types';
import { Settings2, Volume2, Shield, Activity } from 'lucide-react';

interface SettingsPanelProps {
  ttsSettings: TTSSettings;
  setTtsSettings: (settings: TTSSettings) => void;
  isLight: boolean;
  customBg?: string;
  setCustomBg?: (bg: string) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ ttsSettings, setTtsSettings, isLight, customBg, setCustomBg }) => {
  const [testPlaying, setTestPlaying] = React.useState(false);

  const handleTestVoice = async () => {
    if (testPlaying) return;
    setTestPlaying(true);
    try {
      const res = await fetch('http://localhost:3000/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: "System diagnostics nominal. LUNA OS voice systems are online.",
          provider: ttsSettings.provider,
          voiceId: ttsSettings.voiceId,
          elevenLabsApiKey: ttsSettings.elevenLabsApiKey
        })
      });

      if (res.ok) {
        const audioBlob = await res.blob();
        const url = URL.createObjectURL(audioBlob);
        const audio = new Audio(url);
        audio.onended = () => {
          URL.revokeObjectURL(url);
          setTestPlaying(false);
        };
        await audio.play();
      } else {
        console.error("Failed to generate test voice");
        setTestPlaying(false);
      }
    } catch (e) {
      console.error(e);
      setTestPlaying(false);
    }
  };

  const borderClass = isLight ? "border-slate-200" : "border-slate-800";
  const bgClass = isLight ? "bg-white/60" : "bg-slate-900/40";
  const textClass = isLight ? "text-slate-800" : "text-white";
  const subTextClass = isLight ? "text-slate-500" : "text-slate-400";
  const inputClass = isLight ? "bg-white border-slate-300 text-slate-800 placeholder:text-slate-400" : "bg-slate-950/50 border-slate-800 text-slate-200 placeholder:text-slate-600";

  return (
    <div className={`flex flex-col gap-6 p-6 rounded-3xl border ${isLight ? "bg-white/40 border-white/60" : "bg-slate-950/60 border-slate-900"} backdrop-blur-md w-full max-w-4xl mx-auto h-[600px] overflow-y-auto custom-scrollbar`}>
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
          <Settings2 className="w-5 h-5" />
        </div>
        <div>
          <h2 className={`text-xl font-display font-bold ${textClass}`}>System Settings</h2>
          <p className={`text-xs ${subTextClass}`}>Configure Voice Systems, LLM Providers, and System Agent Execution.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* VOICE SETTINGS */}
        <div className={`p-5 rounded-2xl border flex flex-col gap-5 ${bgClass} ${borderClass}`}>
          <div className="flex items-center gap-2 mb-1">
            <Volume2 className="w-4 h-4 text-cyan-400" />
            <h3 className={`text-sm font-bold tracking-widest uppercase ${textClass}`}>Voice Configuration</h3>
          </div>

          <div className="flex flex-col gap-2">
            <label className={`text-xs font-semibold ${subTextClass}`}>TTS Provider</label>
            <select 
              value={ttsSettings.provider}
              onChange={(e) => setTtsSettings({ ...ttsSettings, provider: e.target.value as 'edge' | 'elevenlabs' })}
              className={`text-sm p-2.5 rounded-lg border focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all ${inputClass}`}
            >
              <option value="edge">Edge TTS (Free)</option>
              <option value="elevenlabs">ElevenLabs (Premium)</option>
            </select>
          </div>

          {ttsSettings.provider === 'elevenlabs' && (
            <>
              <div className="flex flex-col gap-2">
                <label className={`text-xs font-semibold ${subTextClass}`}>ElevenLabs API Key</label>
                <input 
                  type="password"
                  placeholder="sk_..."
                  value={ttsSettings.elevenLabsApiKey}
                  onChange={(e) => setTtsSettings({ ...ttsSettings, elevenLabsApiKey: e.target.value })}
                  className={`text-sm p-2.5 rounded-lg border focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all ${inputClass}`}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className={`text-xs font-semibold ${subTextClass}`}>Voice ID</label>
                <input 
                  type="text"
                  placeholder="EXAVITQu4vr4xnSDxMaL"
                  value={ttsSettings.voiceId}
                  onChange={(e) => setTtsSettings({ ...ttsSettings, voiceId: e.target.value })}
                  className={`text-sm p-2.5 rounded-lg border focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all ${inputClass}`}
                />
              </div>
            </>
          )}

          {ttsSettings.provider === 'edge' && (
            <>
              <div className="flex flex-col gap-2">
                <label className={`text-xs font-semibold ${subTextClass}`}>Voice Selection</label>
                <select 
                  value={ttsSettings.voiceId}
                  onChange={(e) => setTtsSettings({ ...ttsSettings, voiceId: e.target.value })}
                  className={`text-sm p-2.5 rounded-lg border focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all ${inputClass}`}
                >
                  <option value="en-US-AriaNeural" className={isLight ? "bg-white text-slate-900" : "bg-slate-900 text-slate-100"}>Aria (Female - US)</option>
                  <option value="en-US-GuyNeural" className={isLight ? "bg-white text-slate-900" : "bg-slate-900 text-slate-100"}>Guy (Male - US)</option>
                  <option value="en-GB-SoniaNeural" className={isLight ? "bg-white text-slate-900" : "bg-slate-900 text-slate-100"}>Sonia (Female - UK)</option>
                  <option value="en-GB-RyanNeural" className={isLight ? "bg-white text-slate-900" : "bg-slate-900 text-slate-100"}>Ryan (Male - UK)</option>
                </select>
              </div>
            </>
          )}

          <div className="pt-2 border-t border-slate-200/10 dark:border-slate-800 mt-2">
            <button 
              onClick={handleTestVoice}
              disabled={testPlaying}
              className={`w-full py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest transition-all ${
                testPlaying 
                  ? "bg-slate-500 text-white cursor-not-allowed" 
                  : "bg-cyan-500 hover:bg-cyan-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]"
              }`}
            >
              {testPlaying ? "Synthesizing..." : "Preview Voice"}
            </button>
          </div>
        </div>

        {/* SYSTEM CONTROL SETTINGS */}
        <div className={`p-5 rounded-2xl border flex flex-col gap-5 ${bgClass} ${borderClass}`}>
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h3 className={`text-sm font-bold tracking-widest uppercase ${textClass}`}>Security & Execution</h3>
          </div>

          <p className={`text-xs leading-relaxed ${subTextClass}`}>
            Luna OS can act as a local system agent, capable of launching applications, updating the OS, and executing commands via <code className="px-1 py-0.5 rounded bg-black/20 text-emerald-400">child_process.exec</code>.
          </p>
          <p className={`text-xs leading-relaxed ${subTextClass}`}>
            Privileged operations (e.g., <code className="px-1 py-0.5 rounded bg-black/20 text-emerald-400">pacman -Syu</code>, <code className="px-1 py-0.5 rounded bg-black/20 text-emerald-400">systemctl</code>) will require explicit user approval and will be run via <code className="px-1 py-0.5 rounded bg-black/20 text-emerald-400">pkexec</code> to invoke the native OS polkit authenticator.
          </p>

          <div className={`mt-auto p-4 rounded-xl border flex items-start gap-3 ${isLight ? "bg-emerald-500/5 border-emerald-500/20" : "bg-emerald-500/10 border-emerald-500/20"}`}>
            <Activity className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
            <div>
              <h4 className={`text-xs font-bold ${isLight ? "text-emerald-700" : "text-emerald-400"}`}>System Agent Active</h4>
              <p className={`text-[10px] mt-1 ${isLight ? "text-emerald-600/80" : "text-emerald-400/70"}`}>Voice commands can directly control your Arch Linux host OS securely.</p>
            </div>
          </div>
        </div>
      </div>

      {/* UI CUSTOMIZATION */}
      <div className={`p-5 rounded-2xl border flex flex-col gap-5 ${bgClass} ${borderClass}`}>
        <div className="flex items-center gap-2 mb-1">
          <Settings2 className="w-4 h-4 text-purple-400" />
          <h3 className={`text-sm font-bold tracking-widest uppercase ${textClass}`}>UI Customization</h3>
        </div>
        <div className="flex flex-col gap-2">
          <label className={`text-xs font-semibold ${subTextClass}`}>Background Image</label>
          <div className="flex items-center gap-4">
            <input 
              type="file" 
              accept="image/*"
              id="bg-upload"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file && setCustomBg) {
                  const reader = new FileReader();
                  reader.onload = (event) => {
                    const dataUrl = event.target?.result as string;
                    setCustomBg(dataUrl);
                    localStorage.setItem('customBg', dataUrl);
                  };
                  reader.readAsDataURL(file);
                }
              }}
            />
            <label 
              htmlFor="bg-upload"
              className={`px-4 py-2 rounded-lg border cursor-pointer text-xs font-semibold transition-all ${
                isLight 
                  ? "bg-white border-slate-300 hover:bg-slate-50 text-slate-700" 
                  : "bg-slate-900 border-slate-700 hover:bg-slate-800 text-slate-200"
              }`}
            >
              Choose Image...
            </label>
            <span className={`text-[10px] ${subTextClass}`}>
              (Max 5MB recommended)
            </span>
          </div>
          {customBg && customBg !== '/background.png' && (
            <button 
              onClick={() => {
                if (setCustomBg) {
                  setCustomBg('/background.png');
                  localStorage.removeItem('customBg');
                }
              }}
              className="text-[10px] text-rose-500 hover:text-rose-400 w-max mt-1"
            >
              Reset to Default Background
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
