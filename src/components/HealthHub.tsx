import React, { useState } from "react";
import { motion } from "motion/react";
import { Activity, Flame, Moon, Footprints, Heart, Compass, Sparkles, Plus, Check } from "lucide-react";
import { HealthData } from "../types";

interface HealthHubProps {
  healthData: HealthData;
  onLogExercise: (type: 'walk' | 'run' | 'sleep' | 'workout') => void;
  isLight?: boolean;
}

export default function HealthHub({
  healthData,
  onLogExercise,
  isLight = false
}: HealthHubProps) {
  const [waterCups, setWaterCups] = useState<number>(4);

  // Helper to compute stroke offsets for circular progress rings
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  
  const getProgressOffset = (current: number, goal: number) => {
    const ratio = Math.min(current / goal, 1);
    return circumference - ratio * circumference;
  };

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 h-full ${isLight ? 'text-slate-800' : 'text-slate-100'}`} id="health-hub-container">
      
      {/* Progress Circles Dashboard (Left column - span 2) */}
      <div className={`lg:col-span-2 flex flex-col gap-6 rounded-2xl p-6 backdrop-blur-md relative overflow-hidden border ${isLight ? 'bg-white/60 border-slate-200/60 shadow-lg' : 'bg-slate-950/60 border-slate-900'}`}>
        <div className={`absolute top-0 right-0 w-64 h-64 blur-3xl pointer-events-none ${isLight ? 'bg-emerald-400/10' : 'bg-emerald-500/5'}`} />

        <div className={`flex items-center justify-between border-b pb-4 ${isLight ? 'border-slate-200' : 'border-slate-900/60'}`}>
          <div>
            <h2 className={`text-md font-semibold font-display flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
              <Activity className="w-4 h-4 text-emerald-500" />
              Health Analytics & Telemetry
            </h2>
            <p className={`text-xs mt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>Biometric sync from wearable sensor nodes is active.</p>
          </div>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${isLight ? 'bg-slate-100 border-slate-200 text-slate-500' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
            REALTIME LOG
          </span>
        </div>

        {/* Circular Gauges Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2 justify-items-center">
          {/* Card 1: Steps */}
          <div className="flex flex-col items-center text-center gap-3">
            <div className="relative w-20 h-20 flex items-center justify-center">
              <svg className="w-full h-full rotate-[-90deg]">
                <circle cx="40" cy="40" r={radius} className={`fill-none ${isLight ? 'stroke-slate-200' : 'stroke-slate-900'}`} strokeWidth="6" />
                <motion.circle 
                  cx="40" 
                  cy="40" 
                  r={radius} 
                  className="stroke-emerald-400 fill-none" 
                  strokeWidth="6" 
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: getProgressOffset(healthData.steps, healthData.stepGoal) }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </svg>
              <div className="absolute text-emerald-500">
                <Footprints className="w-5 h-5" />
              </div>
            </div>
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase">Steps Goal</span>
              <p className={`text-sm font-semibold mt-0.5 ${isLight ? 'text-slate-800' : 'text-white'}`}>{healthData.steps.toLocaleString()}</p>
              <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-400'}`}>/ {healthData.stepGoal.toLocaleString()}</span>
            </div>
          </div>

          {/* Card 2: Calories */}
          <div className="flex flex-col items-center text-center gap-3">
            <div className="relative w-20 h-20 flex items-center justify-center">
              <svg className="w-full h-full rotate-[-90deg]">
                <circle cx="40" cy="40" r={radius} className={`fill-none ${isLight ? 'stroke-slate-200' : 'stroke-slate-900'}`} strokeWidth="6" />
                <motion.circle 
                  cx="40" 
                  cy="40" 
                  r={radius} 
                  className="stroke-orange-500 fill-none" 
                  strokeWidth="6" 
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: getProgressOffset(healthData.calories, healthData.calorieGoal) }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </svg>
              <div className="absolute text-orange-500">
                <Flame className="w-5 h-5" />
              </div>
            </div>
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase">Calories Burn</span>
              <p className={`text-sm font-semibold mt-0.5 ${isLight ? 'text-slate-800' : 'text-white'}`}>{healthData.calories} kcal</p>
              <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-400'}`}>/ {healthData.calorieGoal}</span>
            </div>
          </div>

          {/* Card 3: Distance */}
          <div className="flex flex-col items-center text-center gap-3">
            <div className="relative w-20 h-20 flex items-center justify-center">
              <svg className="w-full h-full rotate-[-90deg]">
                <circle cx="40" cy="40" r={radius} className={`fill-none ${isLight ? 'stroke-slate-200' : 'stroke-slate-900'}`} strokeWidth="6" />
                <motion.circle 
                  cx="40" 
                  cy="40" 
                  r={radius} 
                  className="stroke-cyan-400 fill-none" 
                  strokeWidth="6" 
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: getProgressOffset(healthData.distance, healthData.distanceGoal) }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </svg>
              <div className="absolute text-cyan-500">
                <Compass className="w-5 h-5" />
              </div>
            </div>
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase">Distance</span>
              <p className={`text-sm font-semibold mt-0.5 ${isLight ? 'text-slate-800' : 'text-white'}`}>{healthData.distance.toFixed(1)} miles</p>
              <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-400'}`}>/ {healthData.distanceGoal}</span>
            </div>
          </div>

          {/* Card 4: Sleep */}
          <div className="flex flex-col items-center text-center gap-3">
            <div className="relative w-20 h-20 flex items-center justify-center">
              <svg className="w-full h-full rotate-[-90deg]">
                <circle cx="40" cy="40" r={radius} className={`fill-none ${isLight ? 'stroke-slate-200' : 'stroke-slate-900'}`} strokeWidth="6" />
                <motion.circle 
                  cx="40" 
                  cy="40" 
                  r={radius} 
                  className="stroke-indigo-400 fill-none" 
                  strokeWidth="6" 
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: getProgressOffset(healthData.sleepHours, healthData.sleepGoal) }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </svg>
              <div className="absolute text-indigo-500">
                <Moon className="w-5 h-5" />
              </div>
            </div>
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase">Sleep Cycle</span>
              <p className={`text-sm font-semibold mt-0.5 ${isLight ? 'text-slate-800' : 'text-white'}`}>{healthData.sleepHours} hrs</p>
              <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-400'}`}>/ {healthData.sleepGoal}</span>
            </div>
          </div>
        </div>

        {/* Action Logger / Workout Logger */}
        <div className={`border-t pt-4 mt-2 ${isLight ? 'border-slate-200' : 'border-slate-900/60'}`}>
          <h3 className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-3">Record Biometric Exercises</h3>
          <div className="flex flex-wrap gap-2.5">
            <button
              onClick={() => onLogExercise('walk')}
              className={`flex items-center gap-1.5 px-3 py-1.5 border text-xs font-mono rounded-xl transition-all cursor-pointer ${isLight ? 'bg-white border-slate-200 text-slate-600 hover:text-emerald-600 hover:border-emerald-200 hover:bg-emerald-50' : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-emerald-400 hover:border-emerald-950 hover:bg-emerald-950/20'}`}
            >
              <Plus className="w-3.5 h-3.5" />
              WALK (+1,500 steps)
            </button>
            <button
              onClick={() => onLogExercise('run')}
              className={`flex items-center gap-1.5 px-3 py-1.5 border text-xs font-mono rounded-xl transition-all cursor-pointer ${isLight ? 'bg-white border-slate-200 text-slate-600 hover:text-orange-600 hover:border-orange-200 hover:bg-orange-50' : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-orange-400 hover:border-orange-950 hover:bg-orange-950/20'}`}
            >
              <Plus className="w-3.5 h-3.5" />
              RUN (+3,500 steps)
            </button>
            <button
              onClick={() => onLogExercise('workout')}
              className={`flex items-center gap-1.5 px-3 py-1.5 border text-xs font-mono rounded-xl transition-all cursor-pointer ${isLight ? 'bg-white border-slate-200 text-slate-600 hover:text-cyan-600 hover:border-cyan-200 hover:bg-cyan-50' : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-cyan-400 hover:border-cyan-950 hover:bg-cyan-950/20'}`}
            >
              <Plus className="w-3.5 h-3.5" />
              BIKE (+150 kcal)
            </button>
            <button
              onClick={() => onLogExercise('sleep')}
              className={`flex items-center gap-1.5 px-3 py-1.5 border text-xs font-mono rounded-xl transition-all cursor-pointer ${isLight ? 'bg-white border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-200 hover:bg-indigo-50' : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-indigo-400 hover:border-indigo-950 hover:bg-indigo-950/20'}`}
            >
              <Plus className="w-3.5 h-3.5" />
              ADD REST CYCLE (+1 hr)
            </button>
          </div>
        </div>
      </div>

      {/* Fitness Coach & Heart Rate Diagnostics (Right column - span 1) */}
      <div className="flex flex-col gap-6">
        
        {/* Heart rate & Vitals */}
        <div className={`border rounded-2xl p-5 backdrop-blur-md flex flex-col gap-3 relative ${isLight ? 'bg-white/60 border-slate-200/60 shadow-lg' : 'bg-slate-950/60 border-slate-900'}`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Heart className="w-3.5 h-3.5 text-red-500 animate-pulse" /> Cardiac Index
            </span>
            <span className={`text-xs font-mono font-bold flex items-center gap-1 ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
              <Heart className="w-3 h-3 text-red-500 animate-ping inline-block" /> {healthData.heartRate} BPM
            </span>
          </div>

          <div className={`h-16 flex items-end gap-1 px-1 border rounded-xl p-2.5 ${isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/10 border-slate-900/50'}`}>
            {[45, 50, 48, 62, 85, 74, 60, 55, 68, 70, 64, 58, 80, 92, 75, 62, 58, 66, 68].map((val, idx) => (
              <div
                key={idx}
                className="flex-1 bg-red-500/30 hover:bg-red-500/60 rounded-t transition-colors h-full"
                style={{ height: `${val}%` }}
                title={`${val} bpm`}
              />
            ))}
          </div>
        </div>

        {/* AI Fitness Coach Card */}
        <div className={`border rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex-1 flex flex-col justify-between ${isLight ? 'bg-white/60 border-slate-200/60 shadow-lg' : 'bg-slate-950/60 border-slate-900'}`}>
          <div className={`absolute top-0 right-0 w-32 h-32 blur-2xl pointer-events-none ${isLight ? 'bg-emerald-400/10' : 'bg-emerald-500/5'}`} />
          
          <div className="space-y-3">
            <h3 className={`text-sm font-semibold font-display flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
              <Sparkles className="w-4 h-4 text-emerald-500 animate-pulse" />
              AI Wellness Diagnostics
            </h3>

            <div className={`space-y-3 text-xs leading-relaxed border p-3.5 rounded-xl ${isLight ? 'bg-slate-50/50 border-slate-200 text-slate-700' : 'bg-slate-900/20 border-slate-900/60 text-slate-300'}`}>
              <p>
                <strong>Vitals Report:</strong> Daily metabolic activity is positive. Cardiovascular metrics align with active restoration levels.
              </p>
              <p className={`pt-2.5 border-t ${isLight ? 'text-slate-500 border-slate-200' : 'text-slate-400 border-slate-900/40'}`}>
                <em>Recommendations:</em> Target hydration milestones. Complete the final 1,579 step buffer to finalize steps ring objectives.
              </p>
            </div>
          </div>

          {/* Interactive Hydration Tracker */}
          <div className={`border-t pt-4 mt-4 ${isLight ? 'border-slate-200' : 'border-slate-900/60'}`}>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-mono text-slate-500">HYDRATION RATE: {waterCups}/8 Cups</span>
              <span className="text-cyan-500 font-mono font-medium">{Math.round((waterCups / 8) * 100)}%</span>
            </div>
            
            <div className="flex items-center gap-1.5">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  onClick={() => setWaterCups(Math.max(i + 1, waterCups === i + 1 ? i : i + 1))}
                  className={`h-7 flex-1 border rounded-lg cursor-pointer transition-all flex items-center justify-center ${
                    i < waterCups 
                      ? (isLight ? 'bg-cyan-50 border-cyan-200 text-cyan-600 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'bg-cyan-950/40 border-cyan-800/40 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.1)]') 
                      : (isLight ? 'bg-white border-slate-200 text-slate-300 hover:border-slate-300' : 'bg-slate-900/20 border-slate-900 text-slate-700 hover:border-slate-800')
                  }`}
                >
                  {i < waterCups && <Check className="w-3.5 h-3.5" />}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
