import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Mic, MicOff, Volume2, Cpu, Zap, Radio, RefreshCw, VolumeX, ShieldAlert, Sliders, Activity, Flame } from "lucide-react";
import { CoreState } from "../types";

interface ReactorCoreProps {
  state: CoreState;
  onMicToggle: () => void;
  isListening: boolean;
  transcript: string;
  speechText: string;
  isMuted: boolean;
  onMuteToggle: () => void;
  themeMode?: 'dark' | 'light-glass';
  minimal?: boolean;
}

interface ColorProfile {
  id: string;
  name: string;
  label: string;
  primary: string;
  glow: string;
  glowDark: string;
  accent: string;
  particles: string;
}

const colorProfiles: ColorProfile[] = [
  {
    id: "cyan",
    name: "VIBRANIUM BLUE",
    label: "Mark 85 Core",
    primary: "rgb(6, 182, 212)",
    glow: "rgba(6, 182, 212, 0.5)",
    glowDark: "rgba(6, 182, 212, 0.2)",
    accent: "text-cyan-400",
    particles: "#06b6d4"
  },
  {
    id: "red",
    name: "LUNA RED",
    label: "Protocol Luna",
    primary: "rgb(239, 68, 68)",
    glow: "rgba(239, 68, 68, 0.55)",
    glowDark: "rgba(239, 68, 68, 0.2)",
    accent: "text-red-500",
    particles: "#ef4444"
  },
  {
    id: "purple",
    name: "BLEEDING EDGE",
    label: "Nanosuit Synth",
    primary: "rgb(168, 85, 247)",
    glow: "rgba(168, 85, 247, 0.5)",
    glowDark: "rgba(168, 85, 247, 0.2)",
    accent: "text-purple-400",
    particles: "#a855f7"
  },
  {
    id: "gold",
    name: "ARC AMBER",
    label: "Stark Catalyst",
    primary: "rgb(245, 158, 11)",
    glow: "rgba(245, 158, 11, 0.5)",
    glowDark: "rgba(245, 158, 11, 0.15)",
    accent: "text-amber-400",
    particles: "#f59e0b"
  },
  {
    id: "green",
    name: "GAMMA SYNTH",
    label: "Bio Energy",
    primary: "rgb(34, 197, 94)",
    glow: "rgba(34, 197, 94, 0.45)",
    glowDark: "rgba(34, 197, 94, 0.15)",
    accent: "text-emerald-400",
    particles: "#22c55e"
  },
  {
    id: "orange",
    name: "THERMAL CORE",
    label: "Overcharge Fuel",
    primary: "rgb(249, 115, 22)",
    glow: "rgba(249, 115, 22, 0.5)",
    glowDark: "rgba(249, 115, 22, 0.15)",
    accent: "text-orange-500",
    particles: "#f97316"
  }
];

export default function ReactorCore({
  state,
  onMicToggle,
  isListening,
  transcript,
  speechText,
  isMuted,
  onMuteToggle,
  themeMode = 'dark',
  minimal = false
}: ReactorCoreProps) {
  const [activeProfile, setActiveProfile] = useState<ColorProfile>(colorProfiles[0]);
  const [powerOutput, setPowerOutput] = useState<number>(85); // 0 - 100%
  const [magneticStability, setMagneticStability] = useState<number>(98.4);
  const [coreTemp, setCoreTemp] = useState<number>(42);
  const [isOverloaded, setIsOverloaded] = useState<boolean>(false);
  const [particles, setParticles] = useState<{ id: number; angle: number; speed: number; radius: number; size: number }[]>([]);
  const particleIdRef = useRef(0);

  // Generate particles based on reactor state and power level
  useEffect(() => {
    let particleCount = 20;
    let speedMultiplier = 1;
    
    if (state === "Thinking") {
      particleCount = 35;
      speedMultiplier = 2.2;
    } else if (state === "Executing") {
      particleCount = 50;
      speedMultiplier = 3.5;
    } else if (state === "Listening") {
      particleCount = 25;
      speedMultiplier = 0.8;
    } else if (state === "Offline") {
      particleCount = 4;
      speedMultiplier = 0.1;
    }

    if (isOverloaded) {
      particleCount = 65;
      speedMultiplier *= 2;
    }

    // Adapt based on power slider
    speedMultiplier *= (powerOutput / 85);

    const newParticles = Array.from({ length: particleCount }).map(() => {
      particleIdRef.current += 1;
      return {
        id: particleIdRef.current,
        angle: Math.random() * Math.PI * 2,
        speed: (0.4 + Math.random() * 1.6) * speedMultiplier,
        radius: 35 + Math.random() * 75,
        size: 1.5 + Math.random() * 2.5
      };
    });

    setParticles(newParticles);

    let animationFrame: number;
    const updateParticles = () => {
      setParticles(prev => 
        prev.map(p => {
          let newAngle = p.angle + (p.speed * 0.012);
          let newRadius = p.radius;
          if (state === "Thinking") {
            newRadius = p.radius + Math.sin(newAngle * 4) * 0.4;
          } else if (state === "Executing") {
            newRadius = p.radius - 0.4;
            if (newRadius < 15) newRadius = 110; // reset
          }
          return { ...p, angle: newAngle, radius: newRadius };
        })
      );
      animationFrame = requestAnimationFrame(updateParticles);
    };

    animationFrame = requestAnimationFrame(updateParticles);
    return () => cancelAnimationFrame(animationFrame);
  }, [state, powerOutput, isOverloaded]);

  // Adjust parameters dynamically based on power level
  useEffect(() => {
    setMagneticStability(parseFloat((100 - (powerOutput > 90 ? (powerOutput - 90) * 1.5 : Math.random() * 0.8)).toFixed(1)));
    setCoreTemp(Math.round(35 + (powerOutput * 0.6) + (state === "Thinking" ? 8 : state === "Executing" ? 15 : 0)));
    setIsOverloaded(powerOutput > 95);
  }, [powerOutput, state]);

  // Handle color click
  const selectProfile = (prof: ColorProfile) => {
    setActiveProfile(prof);
  };

  const cycleColorProfile = () => {
    const currentIndex = colorProfiles.findIndex(p => p.id === activeProfile.id);
    const nextIndex = (currentIndex + 1) % colorProfiles.length;
    setActiveProfile(colorProfiles[nextIndex]);
  };

  const isLight = themeMode === 'light-glass';

  return (
    <div 
      className={minimal ? "flex flex-col items-center justify-center relative overflow-visible w-full h-full cursor-pointer" : `flex flex-col items-center justify-between h-full py-6 px-4 relative overflow-hidden transition-all duration-500 ${
        isLight 
          ? "bg-white/40 border border-white/60 shadow-[0_8px_32px_0_rgba(31,38,135,0.06)] backdrop-blur-xl text-slate-800" 
          : "bg-slate-950/20 border border-slate-900/80 text-white"
      }`} 
      id="luna-reactor-hud"
      onClick={cycleColorProfile}
    >
      
      {!minimal && (
        <>
          {/* Premium background styling based on theme */}
          {!isLight ? (
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-950 via-slate-950 to-black z-0" />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-tr from-sky-50/10 via-white/5 to-indigo-50/10 z-0" />
          )}
          
          {/* Spatial glass reflection */}
          <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-white/[0.05] to-transparent pointer-events-none z-10" />

          {/* Title & Luna Mode Header */}
          <div className="z-20 text-center w-full select-none pt-1">
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] tracking-widest font-mono border transition-all duration-300 ${
              isLight 
                ? "bg-white/70 border-slate-200/60 text-slate-500 shadow-sm" 
                : "bg-slate-900/80 border-slate-800/80 text-slate-400"
            }`}>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: activeProfile.primary }} />
                <span className="relative inline-flex rounded-full h-2 w-2" style={{ backgroundColor: activeProfile.primary }} />
              </span>
              LUNA INTUITIVE NET // CORE ARC V4
            </div>
            
            <h1 className={`text-xl md:text-2xl font-bold tracking-tight mt-3 font-display transition-colors ${
              isLight ? "text-slate-900" : "text-white"
            }`}>
              Luna Command Center
            </h1>
            <p className={`text-xs mt-1 max-w-sm mx-auto ${isLight ? "text-slate-500" : "text-slate-400"}`}>
              Interact with Luna's holographic Arc Reactor. Adjust power density, swap visual matrix grids, or prompt vocal commands.
            </p>
          </div>
        </>
      )}

      {/* THE ARC REACTOR MASTER FRAME */}
      <div className="relative w-76 h-76 md:w-80 md:h-80 flex items-center justify-center z-20 my-6">
        
        {/* Dynamic Glowing Dust Clouds */}
        <div className="absolute inset-0 pointer-events-none">
          {particles.map(p => {
            const x = Math.cos(p.angle) * p.radius;
            const y = Math.sin(p.angle) * p.radius;
            return (
              <motion.div
                key={p.id}
                className="absolute rounded-full"
                style={{
                  left: "50%",
                  top: "50%",
                  width: `${p.size}px`,
                  height: `${p.size}px`,
                  x,
                  y,
                  backgroundColor: activeProfile.particles,
                  boxShadow: `0 0 8px ${activeProfile.primary}`,
                  opacity: state === "Offline" ? 0.15 : isOverloaded ? 0.95 : 0.7
                }}
              />
            );
          })}
        </div>

        {/* Ambient Back Glow */}
        <motion.div
          className="absolute w-64 h-64 rounded-full blur-3xl pointer-events-none transition-all duration-700"
          style={{
            background: `radial-gradient(circle, ${activeProfile.glow} 0%, transparent 70%)`
          }}
          animate={{
            scale: state === "Thinking" ? [1, 1.15, 1] : state === "Executing" ? [1.1, 1.25, 1.1] : [0.95, 1.05, 0.95]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        {/* 1. Concentric Tech Outer Ring with HUD Ticks */}
        <div className={`absolute inset-0 border rounded-full border-dashed animate-[spin_80s_linear_infinite] p-1 ${
          isLight ? 'border-slate-300' : 'border-slate-800'
        }`} />

        {/* 2. Counter-Rotating Gear Ring */}
        <motion.div 
          className={`absolute inset-4 border rounded-full border-dotted ${
            isLight ? 'border-slate-300' : 'border-slate-700/60'
          }`}
          style={{ originX: 0.5, originY: 0.5 }}
          animate={{ rotate: -360 }}
          transition={{ duration: 40 - (powerOutput / 3), repeat: Infinity, ease: "linear" }}
        />

        {/* 3. 10 COPPER COIL ARC WEDGES (AUTHENTIC IRON MAN STYLE) */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {Array.from({ length: 10 }).map((_, i) => {
            const angle = i * 36;
            return (
              <div
                key={i}
                className="absolute origin-center w-8 h-12 flex flex-col items-center justify-between"
                style={{
                  transform: `rotate(${angle}deg) translateY(-85px)`,
                }}
              >
                {/* Copper coil block wrapping */}
                <div 
                  className={`w-6 h-3 rounded-sm border transition-all duration-500 shadow-md ${
                    isOverloaded 
                      ? "bg-amber-400 border-amber-300 shadow-[0_0_12px_rgba(251,191,36,0.8)]"
                      : "bg-amber-600/90 border-amber-500/50"
                  }`} 
                  style={{
                    boxShadow: isOverloaded ? "" : `0 0 6px ${activeProfile.glowDark}`
                  }}
                />
                
                {/* Core LED emitter node below copper loop */}
                <motion.div
                  className="w-4 h-2 rounded-full transition-colors duration-500"
                  style={{
                    backgroundColor: activeProfile.primary,
                    boxShadow: `0 0 8px ${activeProfile.primary}`
                  }}
                  animate={{
                    opacity: state === "Listening" ? [0.4, 1, 0.4] : [0.7, 1, 0.7]
                  }}
                  transition={{
                    duration: 1.5 + (i * 0.1),
                    repeat: Infinity
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* 4. Concentric Tech Housing ring with hex slots */}
        <div className={`absolute w-38 h-38 rounded-full border-2 ${
          isLight ? 'border-slate-200 bg-white/20' : 'border-slate-800 bg-slate-950/40'
        } flex items-center justify-center`} />

        {/* 5. INTERACTIVE MULTI-FACETED Luna Triangular Center Core */}
        <motion.div
          className={`absolute w-28 h-28 rounded-full flex items-center justify-center cursor-pointer group z-30`}
          onClick={(e) => {
            e.stopPropagation();
            onMicToggle();
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            boxShadow: `0 8px 32px 0 ${activeProfile.glowDark}`
          }}
        >
          {/* Inner holographic rotating tech track */}
          <motion.div 
            className="absolute inset-1 border border-dashed rounded-full"
            style={{ borderColor: activeProfile.primary }}
            animate={{ rotate: 360 }}
            transition={{ duration: 15 - (powerOutput / 8), repeat: Infinity, ease: "linear" }}
          />

          {/* Core Energy Glass Orb */}
          <div className={`w-20 h-20 rounded-full flex flex-col items-center justify-center relative overflow-hidden transition-all duration-500 ${
            isLight ? "bg-white/80 border border-white" : "bg-slate-900 border border-slate-800"
          }`}>
            
            {/* Ambient dynamic pulse mask */}
            <motion.div 
              className="absolute inset-0 rounded-full pointer-events-none"
              style={{
                background: `radial-gradient(circle, ${activeProfile.glow} 0%, transparent 80%)`,
              }}
              animate={{
                opacity: [0.3, 0.75, 0.3]
              }}
              transition={{
                duration: state === "Thinking" ? 0.8 : 2.5,
                repeat: Infinity
              }}
            />

            {/* Glowing angular HUD icon layout */}
            <AnimatePresence mode="wait">
              <motion.div
                key={state}
                initial={{ scale: 0.4, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.4, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="z-10 drop-shadow-lg"
                style={{ color: activeProfile.primary }}
              >
                {state === "Listening" && <Mic className="w-7 h-7 animate-pulse" />}
                {state === "Thinking" && <RefreshCw className="w-7 h-7 animate-spin" />}
                {state === "Speaking" && <Volume2 className="w-7 h-7 animate-bounce" />}
                {state === "Executing" && <Zap className="w-7 h-7 animate-pulse" />}
                {state === "Warning" && <ShieldAlert className="w-7 h-7 text-red-500" />}
                {state === "Idle" && <Radio className="w-7 h-7 hover:scale-110 transition-transform" />}
                {state === "Offline" && <MicOff className="w-7 h-7 text-slate-400" />}
              </motion.div>
            </AnimatePresence>

            {/* Audio frequencies running across bottom part of the glass orb */}
            {(state === "Listening" || state === "Speaking") && (
              <div className="absolute bottom-2.5 flex justify-center items-end gap-0.5 h-4 w-12 z-10">
                {Array.from({ length: 6 }).map((_, idx) => (
                  <motion.div
                    key={idx}
                    className="w-0.5 rounded-full"
                    style={{ backgroundColor: activeProfile.primary }}
                    animate={{
                      height: state === "Listening" 
                        ? [3, 9 + Math.random() * 8, 3] 
                        : [3, 6 + Math.random() * 10, 3]
                    }}
                    transition={{
                      duration: 0.15 + idx * 0.04,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Orbit Node indicators floating around outer rims */}
        <motion.div 
          className="absolute w-2 h-2 rounded-full"
          style={{ x: 120, y: 0, backgroundColor: activeProfile.primary }}
          animate={{ rotate: 360 }}
          transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
        />
        <motion.div 
          className="absolute w-1.5 h-1.5 rounded-full bg-amber-400"
          style={{ x: -110, y: -30 }}
          animate={{ rotate: -360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        />
      </div>

      {/* INTERACTIVE CONTROLS SECTION */}
      {!minimal && (
        <div className="z-20 w-full max-w-lg flex flex-col gap-4">
          
          {/* Dynamic Color Matrix Picker (Luna type visual subroutine swap) */}
          <div className={`p-3 rounded-2xl border ${
            isLight ? "bg-white/60 border-slate-200/60 shadow-sm" : "bg-slate-900/40 border-slate-900/60"
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-[10px] font-mono font-semibold uppercase tracking-wider flex items-center gap-1 ${
                isLight ? "text-slate-600" : "text-slate-300"
              }`}>
                <Flame className="w-3.5 h-3.5" style={{ color: activeProfile.primary }} />
                Arc Visual Array
              </span>
              <span className="text-[9px] font-mono px-2 py-0.5 bg-slate-850 border border-slate-800 text-slate-400 rounded-md uppercase tracking-wider">
                {activeProfile.name}
              </span>
            </div>

            <div className="grid grid-cols-6 gap-2">
              {colorProfiles.map(prof => {
                const isActive = activeProfile.id === prof.id;
                return (
                  <button
                    key={prof.id}
                    onClick={() => selectProfile(prof)}
                    className={`relative h-9 rounded-xl flex items-center justify-center cursor-pointer transition-all border ${
                      isActive 
                        ? "border-slate-400 scale-105 shadow-md" 
                        : "border-transparent hover:scale-105"
                    } ${isLight ? "bg-white/80" : "bg-slate-950/80"}`}
                    title={prof.name}
                  >
                    <div 
                      className="h-4.5 w-4.5 rounded-full transition-transform duration-300" 
                      style={{ 
                        backgroundColor: prof.primary,
                        boxShadow: isActive ? `0 0 10px ${prof.primary}` : 'none',
                        transform: isActive ? 'scale(1.15)' : 'scale(1)'
                      }} 
                    />
                    {isActive && (
                      <motion.div 
                        layoutId="activeColorBorder"
                        className="absolute inset-0 rounded-xl border-2"
                        style={{ borderColor: prof.primary }}
                      />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Reactor Power & Voltage HUD Panel */}
          <div className={`grid grid-cols-2 gap-3`}>
            
            {/* Output Voltage adjust panel */}
            <div className={`p-3 rounded-xl border flex flex-col justify-between ${
              isLight ? "bg-white/60 border-slate-200/60 text-slate-700" : "bg-slate-900/40 border-slate-900/60 text-slate-300"
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-wide">
                <span>Reactor Core Density</span>
                <span className="font-semibold" style={{ color: activeProfile.primary }}>{powerOutput}%</span>
              </div>
              
              <input 
                type="range"
                min="20"
                max="110"
                value={powerOutput}
                onChange={(e) => setPowerOutput(parseInt(e.target.value))}
                className="w-full h-1 my-3 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                style={{ accentColor: activeProfile.primary }}
              />
              
              <div className="flex items-center justify-between text-[9px] font-mono text-slate-400">
                <span>{coreTemp}°C THERMAL</span>
                <span>{isOverloaded ? "OVERLOADED" : "NOMINAL"}</span>
              </div>
            </div>

            {/* Diagnostic Subroutines */}
            <div className={`p-3 rounded-xl border flex flex-col justify-between ${
              isLight ? "bg-white/60 border-slate-200/60 text-slate-700" : "bg-slate-900/40 border-slate-900/60 text-slate-300"
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase">
                <span>Shield Ring Stability</span>
                <span className="font-semibold">{magneticStability}%</span>
              </div>

              <div className="flex gap-1 items-center my-1.5 h-4">
                <span className="h-1 w-1 rounded-full bg-slate-600" />
                <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500" 
                    style={{ 
                      width: `${magneticStability}%`,
                      backgroundColor: activeProfile.primary 
                    }} 
                  />
                </div>
              </div>

              <div className="flex justify-between items-center text-[9px] font-mono text-slate-400">
                <span>FREQ: {(powerOutput * 12.5).toFixed(0)} MHz</span>
                <span className={`h-2 w-2 rounded-full ${isOverloaded ? "bg-red-500 animate-ping" : "bg-emerald-500"}`} />
              </div>
            </div>
          </div>

          {/* Transcription Feedback overlay screen */}
          <div className={`p-4 rounded-2xl border relative transition-all ${
            isLight ? "bg-white/75 border-slate-200/70" : "bg-slate-950/80 border-slate-900"
          }`}>
            <div className="absolute top-2.5 right-4 flex items-center gap-1.5">
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest bg-slate-800/10 dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200/40">
                WAKE WORD: LUNA
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            </div>

            <div className="text-left">
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-2">
                <Activity className="w-3.5 h-3.5" style={{ color: activeProfile.primary }} />
                Live Diagnostics Telemetry
              </div>
              
              <div className="min-h-12 flex flex-col justify-center mt-2">
                {isListening ? (
                  <p className="text-sm font-sans italic font-medium" style={{ color: activeProfile.primary }}>
                    {transcript || "Listening for secure vocal commands..."}
                  </p>
                ) : speechText ? (
                  <div className="space-y-1">
                    <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">LUNA RESPONSE</p>
                    <p className={`text-sm leading-relaxed font-sans font-medium ${isLight ? "text-slate-800" : "text-slate-100"}`}>
                      {speechText}
                    </p>
                  </div>
                ) : (
                  <p className={`text-xs font-mono italic ${isLight ? "text-slate-500" : "text-slate-400"}`}>
                    System Grid: <span className="font-semibold" style={{ color: activeProfile.primary }}>{activeProfile.label}</span> is armed. Try saying: "sync workstation" or click reactor core to speak.
                  </p>
                )}
              </div>
            </div>

            {/* Capture Trigger Bar */}
            <div className="border-t border-slate-200/30 dark:border-slate-900 mt-3 pt-2 flex items-center justify-between gap-4">
              <button 
                onClick={onMicToggle}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-mono font-medium tracking-wide transition-all duration-300 cursor-pointer ${
                  isListening 
                    ? 'bg-red-50 text-red-500 border border-red-200 shadow-[0_0_15px_rgba(239,68,68,0.2)]' 
                    : isLight
                      ? 'bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700'
                      : 'bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700'
                }`}
              >
                {isListening ? (
                  <>
                    <Mic className="w-4 h-4 text-red-500 animate-pulse" />
                    <span>VOICE LINK OPEN</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4 text-slate-500" />
                    <span>ENGAGE MICROPHONE</span>
                  </>
                )}
              </button>

              <button 
                onClick={onMuteToggle}
                className={`p-2 rounded-xl transition-all border cursor-pointer ${
                  isLight ? "bg-slate-100 border-slate-200 text-slate-500 hover:text-slate-900" : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                }`}
                title={isMuted ? "Unmute neural voice feedback" : "Mute neural voice feedback"}
              >
                {isMuted ? <VolumeX className="w-4 h-4 text-red-500" /> : <Volume2 className="w-4 h-4" />}
              </button>
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
