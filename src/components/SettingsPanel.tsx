import React, { useState } from 'react';
import { TTSSettings } from '../types';
import { Settings2, Volume2, Shield, Activity, Database, Server, Key, Eye, EyeOff, Layout } from 'lucide-react';

interface SettingsPanelProps {
  settingsConfig: any;
  setSettingsConfig: (config: any) => void;
  ttsSettings: TTSSettings;
  setTtsSettings: (settings: TTSSettings) => void;
  isLight: boolean;
  customBg?: string;
  setCustomBg?: (bg: string) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  settingsConfig,
  setSettingsConfig,
  ttsSettings,
  setTtsSettings,
  isLight,
  customBg,
  setCustomBg
}) => {
  const [testPlaying, setTestPlaying] = useState(false);
  const [showKeys, setShowKeys] = useState<{ [key: string]: boolean }>({});

  const toggleShowKey = (key: string) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

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

  const handleSaveAll = () => {
    localStorage.setItem("settingsConfig", JSON.stringify(settingsConfig));
    localStorage.setItem("groqKey", settingsConfig.groqKey || "");
    localStorage.setItem("openRouterKey", settingsConfig.openRouterKey || "");
    localStorage.setItem("openaiKey", settingsConfig.openaiKey || "");
    localStorage.setItem("githubPat", settingsConfig.githubPat || "");
    localStorage.setItem("ttsSettings", JSON.stringify(ttsSettings));
    localStorage.setItem("elevenLabsKey", ttsSettings.elevenLabsApiKey || "");
    alert("Luna System Configurations Saved Successfully!");
  };

  const borderClass = isLight ? "border-slate-200" : "border-slate-800/80";
  const cardBgClass = isLight ? "bg-white/60 shadow-sm" : "bg-slate-900/40 backdrop-blur-sm";
  const textClass = isLight ? "text-slate-800" : "text-white";
  const subTextClass = isLight ? "text-slate-500" : "text-slate-400";
  const labelClass = `text-xs font-semibold ${isLight ? "text-slate-700" : "text-slate-300"}`;
  
  const inputClass = isLight 
    ? "bg-white border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500" 
    : "bg-slate-950/60 border-slate-800/80 text-slate-200 placeholder:text-slate-650 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500";

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* CARD 1: VOICE CONFIGURATION */}
        <div className={`p-5 rounded-2xl border flex flex-col gap-4 ${cardBgClass} ${borderClass}`}>
          <div className="flex items-center gap-2 pb-2 border-b border-slate-200/10">
            <Volume2 className="w-4 h-4 text-cyan-400" />
            <h3 className={`text-xs font-bold tracking-wider uppercase font-mono ${textClass}`}>Voice Configuration</h3>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className={labelClass}>Wake Word Trigger</label>
            <select 
              value={settingsConfig.wakeWord}
              onChange={(e) => setSettingsConfig({ ...settingsConfig, wakeWord: e.target.value })}
              className={`text-xs p-2 rounded-lg border outline-none transition-all ${inputClass}`}
            >
              <option value="LUNA">"LUNA"</option>
              <option value="COMPUTER">"COMPUTER"</option>
              <option value="SYSTEM">"SYSTEM"</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className={labelClass}>TTS Provider</label>
            <select 
              value={ttsSettings.provider}
              onChange={(e) => setTtsSettings({ ...ttsSettings, provider: e.target.value as 'edge' | 'elevenlabs' })}
              className={`text-xs p-2 rounded-lg border outline-none transition-all ${inputClass}`}
            >
              <option value="edge">Edge TTS (Free)</option>
              <option value="elevenlabs">ElevenLabs (Premium)</option>
            </select>
          </div>

          {ttsSettings.provider === 'elevenlabs' ? (
            <>
              <div className="flex flex-col gap-1.5">
                <label className={labelClass}>ElevenLabs API Key</label>
                <div className="relative">
                  <input 
                    type={showKeys['eleven'] ? "text" : "password"}
                    placeholder="sk_..."
                    value={ttsSettings.elevenLabsApiKey}
                    onChange={(e) => setTtsSettings({ ...ttsSettings, elevenLabsApiKey: e.target.value })}
                    className={`text-xs p-2 pr-9 w-full rounded-lg border outline-none transition-all ${inputClass}`}
                  />
                  <button 
                    type="button"
                    onClick={() => toggleShowKey('eleven')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showKeys['eleven'] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className={labelClass}>Voice ID</label>
                <input 
                  type="text"
                  placeholder="EXAVITQu4vr4xnSDxMaL"
                  value={ttsSettings.voiceId}
                  onChange={(e) => setTtsSettings({ ...ttsSettings, voiceId: e.target.value })}
                  className={`text-xs p-2 rounded-lg border outline-none transition-all ${inputClass}`}
                />
              </div>
            </>
          ) : (
            <div className="flex flex-col gap-1.5">
              <label className={labelClass}>Voice Selection</label>
              <select 
                value={ttsSettings.voiceId}
                onChange={(e) => setTtsSettings({ ...ttsSettings, voiceId: e.target.value })}
                className={`text-xs p-2 rounded-lg border outline-none transition-all ${inputClass}`}
              >
                <option value="en-US-AriaNeural">Aria (Female - US)</option>
                <option value="en-US-GuyNeural">Guy (Male - US)</option>
                <option value="en-GB-SoniaNeural">Sonia (Female - UK)</option>
                <option value="en-GB-RyanNeural">Ryan (Male - UK)</option>
              </select>
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs">
              <label className={labelClass}>Speech Speed: {settingsConfig.speechRate}x</label>
            </div>
            <input 
              type="range"
              min="0.5"
              max="1.5"
              step="0.1"
              value={settingsConfig.speechRate}
              onChange={(e) => setSettingsConfig({ ...settingsConfig, speechRate: parseFloat(e.target.value) })}
              className="w-full accent-cyan-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>

          <button 
            onClick={handleTestVoice}
            disabled={testPlaying}
            className={`w-full mt-2 py-2 rounded-xl font-bold text-xs uppercase tracking-wider transition-all ${
              testPlaying 
                ? "bg-slate-650 text-white cursor-not-allowed" 
                : "bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-600/20"
            }`}
          >
            {testPlaying ? "Synthesizing..." : "Preview Voice"}
          </button>
        </div>

        {/* CARD 2: AI MODEL ROUTING */}
        <div className={`p-5 rounded-2xl border flex flex-col gap-4 ${cardBgClass} ${borderClass}`}>
          <div className="flex items-center gap-2 pb-2 border-b border-slate-200/10">
            <Database className="w-4 h-4 text-purple-400" />
            <h3 className={`text-xs font-bold tracking-wider uppercase font-mono ${textClass}`}>AI Model Configuration</h3>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className={labelClass}>Active Provider</label>
            <select 
              value={settingsConfig.activeProvider || "groq"}
              onChange={(e) => setSettingsConfig({ ...settingsConfig, activeProvider: e.target.value })}
              className={`text-xs p-2 rounded-lg border outline-none transition-all ${inputClass}`}
            >
              <option value="gemini">Gemini (Studio)</option>
              <option value="groq">Groq Cloud</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="local">Local LLM (Ollama)</option>
              <option value="openclaw">Open Claw Gateway</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className={labelClass}>Model Override Selection</label>
            <input 
              type="text"
              value={settingsConfig.modelSelection}
              onChange={(e) => setSettingsConfig({ ...settingsConfig, modelSelection: e.target.value })}
              placeholder="e.g. llama3-70b-8192, gpt-4o, gemini-2.5-flash"
              className={`text-xs p-2 rounded-lg border outline-none transition-all ${inputClass}`}
            />
            <p className="text-[10px] text-slate-500 font-mono">Leave empty for provider-specific defaults.</p>
          </div>

          <div className="p-3.5 rounded-xl border border-dashed border-slate-800 bg-black/10 text-xs flex flex-col gap-2 mt-auto">
            <span className="font-mono text-cyan-400 font-semibold uppercase text-[10px]">Model Performance Matrix</span>
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-400">
              <div>Groq: <span className="text-emerald-400">Ultra-low latency</span></div>
              <div>Gemini: <span className="text-purple-400">Advanced analysis</span></div>
              <div>Local: <span className="text-orange-400">Privacy focused</span></div>
              <div>Claw: <span className="text-yellow-400">Agent integration</span></div>
            </div>
          </div>
        </div>

        {/* CARD 3: CONNECTORS & CREDENTIALS */}
        <div className={`p-5 rounded-2xl border flex flex-col gap-4 md:col-span-2 ${cardBgClass} ${borderClass}`}>
          <div className="flex items-center gap-2 pb-2 border-b border-slate-200/10">
            <Key className="w-4 h-4 text-emerald-400" />
            <h3 className={`text-xs font-bold tracking-wider uppercase font-mono ${textClass}`}>Connectors & API Credentials</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Cloud Credentials */}
            <div className="flex flex-col gap-3.5">
              <h4 className="text-[11px] font-bold tracking-wider font-mono text-slate-400 uppercase">Cloud API Keys</h4>
              
              <div className="flex flex-col gap-1.5">
                <label className={labelClass}>Groq API Key</label>
                <div className="relative">
                  <input 
                    type={showKeys['groq'] ? "text" : "password"}
                    value={settingsConfig.groqKey || ""}
                    onChange={(e) => setSettingsConfig({ ...settingsConfig, groqKey: e.target.value })}
                    placeholder="gsk_..."
                    className={`text-xs p-2 pr-9 w-full rounded-lg border outline-none transition-all ${inputClass}`}
                  />
                  <button type="button" onClick={() => toggleShowKey('groq')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500">
                    {showKeys['groq'] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className={labelClass}>OpenAI API Key</label>
                <div className="relative">
                  <input 
                    type={showKeys['openai'] ? "text" : "password"}
                    value={settingsConfig.openaiKey || ""}
                    onChange={(e) => setSettingsConfig({ ...settingsConfig, openaiKey: e.target.value })}
                    placeholder="sk-..."
                    className={`text-xs p-2 pr-9 w-full rounded-lg border outline-none transition-all ${inputClass}`}
                  />
                  <button type="button" onClick={() => toggleShowKey('openai')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500">
                    {showKeys['openai'] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className={labelClass}>OpenRouter API Key</label>
                <div className="relative">
                  <input 
                    type={showKeys['openrouter'] ? "text" : "password"}
                    value={settingsConfig.openRouterKey || ""}
                    onChange={(e) => setSettingsConfig({ ...settingsConfig, openRouterKey: e.target.value })}
                    placeholder="sk-or-v1-..."
                    className={`text-xs p-2 pr-9 w-full rounded-lg border outline-none transition-all ${inputClass}`}
                  />
                  <button type="button" onClick={() => toggleShowKey('openrouter')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500">
                    {showKeys['openrouter'] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className={labelClass}>GitHub PAT (Personal Access Token)</label>
                <div className="relative">
                  <input 
                    type={showKeys['github'] ? "text" : "password"}
                    value={settingsConfig.githubPat || ""}
                    onChange={(e) => setSettingsConfig({ ...settingsConfig, githubPat: e.target.value })}
                    placeholder="ghp_..."
                    className={`text-xs p-2 pr-9 w-full rounded-lg border outline-none transition-all ${inputClass}`}
                  />
                  <button type="button" onClick={() => toggleShowKey('github')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500">
                    {showKeys['github'] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Local & Open Claw Connectors */}
            <div className="flex flex-col gap-3.5 border-t md:border-t-0 md:border-l border-slate-200/10 pt-4 md:pt-0 md:pl-4">
              <h4 className="text-[11px] font-bold tracking-wider font-mono text-slate-400 uppercase">Local & Custom Gateways</h4>
              
              {/* Local LLM Ollama Connection */}
              <div className="flex flex-col gap-2 p-3 rounded-xl border border-slate-800 bg-slate-950/20">
                <div className="flex items-center justify-between">
                  <span className={labelClass}>Ollama Local LLM Link</span>
                  <button 
                    type="button"
                    onClick={() => setSettingsConfig({ ...settingsConfig, isLocalLlm: !settingsConfig.isLocalLlm })}
                    className={`h-4.5 w-9 rounded-full flex items-center p-0.5 transition-colors ${settingsConfig.isLocalLlm ? 'bg-orange-500' : 'bg-slate-800'}`}
                  >
                    <div className={`h-3.5 w-3.5 rounded-full bg-white transition-transform ${settingsConfig.isLocalLlm ? 'translate-x-4.5' : ''}`} />
                  </button>
                </div>
                
                {settingsConfig.isLocalLlm && (
                  <div className="flex flex-col gap-2 mt-1.5">
                    <input 
                      type="text" 
                      placeholder="Endpoint: http://localhost:11434"
                      value={settingsConfig.localLlmUrl || ""}
                      onChange={(e) => setSettingsConfig({ ...settingsConfig, localLlmUrl: e.target.value })}
                      className={`text-[10px] p-2 rounded border outline-none ${inputClass}`}
                    />
                    <input 
                      type="text" 
                      placeholder="Model Name: e.g. llama3"
                      value={settingsConfig.localLlmModel || ""}
                      onChange={(e) => setSettingsConfig({ ...settingsConfig, localLlmModel: e.target.value })}
                      className={`text-[10px] p-2 rounded border outline-none ${inputClass}`}
                    />
                  </div>
                )}
              </div>

              {/* Open Claw Connector */}
              <div className="flex flex-col gap-2 p-3 rounded-xl border border-slate-800 bg-slate-950/20">
                <span className={labelClass}>Open Claw Agent Connector</span>
                <div className="flex flex-col gap-2 mt-1">
                  <input 
                    type="text" 
                    placeholder="Claw Endpoint: http://localhost:8000/v1"
                    value={settingsConfig.openClawUrl || ""}
                    onChange={(e) => setSettingsConfig({ ...settingsConfig, openClawUrl: e.target.value })}
                    className={`text-[10px] p-2 rounded border outline-none ${inputClass}`}
                  />
                  <input 
                    type="password" 
                    placeholder="Claw API Key"
                    value={settingsConfig.openClawApiKey || ""}
                    onChange={(e) => setSettingsConfig({ ...settingsConfig, openClawApiKey: e.target.value })}
                    className={`text-[10px] p-2 rounded border outline-none ${inputClass}`}
                  />
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* CARD 4: SYSTEM AGENT & CUSTOMIZATION */}
        <div className={`p-5 rounded-2xl border flex flex-col gap-4 md:col-span-2 ${cardBgClass} ${borderClass}`}>
          <div className="flex items-center gap-2 pb-2 border-b border-slate-200/10">
            <Shield className="w-4 h-4 text-orange-400" />
            <h3 className={`text-xs font-bold tracking-wider uppercase font-mono ${textClass}`}>System Security & Customization</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* System Agent Controls */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className={labelClass}>Interactive Core Glow</p>
                  <p className="text-[10px] text-slate-500">Enable high-performance shaders in background.</p>
                </div>
                <button 
                  onClick={() => setSettingsConfig({ ...settingsConfig, ambientGlow: !settingsConfig.ambientGlow })}
                  className={`h-5 w-10 rounded-full flex items-center p-0.5 transition-colors cursor-pointer ${
                    settingsConfig.ambientGlow ? 'bg-cyan-500' : 'bg-slate-800'
                  }`}
                >
                  <div className={`h-4 w-4 rounded-full bg-white transition-transform ${settingsConfig.ambientGlow ? 'translate-x-5' : ''}`} />
                </button>
              </div>

              <div className="p-3 rounded-xl bg-orange-500/5 border border-orange-500/20 text-[11px] leading-relaxed text-slate-400 flex items-start gap-2.5">
                <Activity className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-orange-400">Environment Abstraction Broker: ACTIVE</span>
                  <p className="mt-0.5">Luna OS acts as a secure system broker. Handlers automatically detect your workspace parameters and apply desktop management routines.</p>
                </div>
              </div>
            </div>

            {/* UI Background Image upload */}
            <div className="flex flex-col gap-2">
              <label className={labelClass}>Global Wallpaper Customization</label>
              <div className="flex items-center gap-3">
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
                  className={`px-3 py-2 rounded-lg border cursor-pointer text-[11px] font-semibold transition-all ${
                    isLight 
                      ? "bg-white border-slate-200 hover:bg-slate-50 text-slate-700" 
                      : "bg-slate-900 border-slate-800 hover:bg-slate-800 text-slate-200"
                  }`}
                >
                  Choose Custom Image...
                </label>
                <span className="text-[10px] text-slate-500 font-mono">(Max 5MB)</span>
              </div>
              {customBg && customBg !== '/background.png' && (
                <button 
                  onClick={() => {
                    if (setCustomBg) {
                      setCustomBg('/background.png');
                      localStorage.removeItem('customBg');
                    }
                  }}
                  className="text-[10px] text-rose-500 hover:text-rose-400 w-max mt-1 font-mono"
                >
                  Reset to Default Background
                </button>
              )}
            </div>

          </div>
        </div>

      </div>

      {/* FOOTER SAVE PANEL */}
      <div className={`flex justify-end p-4 border-t ${borderClass} mt-4`}>
        <button 
          onClick={handleSaveAll}
          className="px-8 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-bold text-xs uppercase tracking-widest transition-all shadow-lg shadow-cyan-600/20"
        >
          Save All System Configurations
        </button>
      </div>
    </div>
  );
};
