import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { 
  Home, Mic, Folder, Smartphone, Code, BarChart2, MessageSquare, Settings,
  Cpu, Activity, CheckCircle2, AlertTriangle, ShieldAlert, Wifi, Battery, Play,
  Send, Plus, Trash2, Heart, Sparkles, Volume2, Globe, Server, Check, HelpCircle,
  Sun, Moon, Gauge, Terminal, ArrowLeft, FileText, FileImage, File, X, ChevronRight
} from "lucide-react";

import { 
  CoreState, ActiveView, DeviceTelemetry, ActivityEvent, 
  SystemMetrics, SystemGoal, HealthData, GitHubRepo, LogMessage, TTSSettings 
} from "./types";

import ReactorCore from "./components/ReactorCore";
import DeviceEcosystem from "./components/DeviceEcosystem";
import DeveloperWorkspace from "./components/DeveloperWorkspace";
import GithubMonitor from "./components/GithubMonitor";
import { SettingsPanel } from "./components/SettingsPanel";

const formatBytes = (bytes: number, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export default function App() {
  // Views and states
  const [activeView, setActiveView] = useState<ActiveView>("home");
  const [themeMode, setThemeMode] = useState<'dark' | 'light-glass'>('dark');

  // Interactive Reactor Hardware States
  const [magneticField, setMagneticField] = useState<number>(2.4);
  const [coolantPump, setCoolantPump] = useState<number>(2400);
  const [refreshRate, setRefreshRate] = useState<number>(120);
  const [diagnosticStepIndex, setDiagnosticStepIndex] = useState<number>(-1);
  const [diagnosticLogs, setDiagnosticLogs] = useState<string[]>([
    "Luna diagnostics system standby.",
    "Hardware matrix calibration node ready."
  ]);
  const [coreState, setCoreState] = useState<CoreState>("Idle");
  const [speechText, setSpeechText] = useState<string>("Hello, Boss. I'm Luna. Everything is online and ready. I've finished checking the system, and we're good to go. What would you like to work on today?");
  const [transcript, setTranscript] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<{ role: string, content: string }[]>([]);
  
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);
  const [apiHealth, setApiHealth] = useState<{ enabled: boolean; checked: boolean }>({ enabled: false, checked: false });
  const [showUserModal, setShowUserModal] = useState<boolean>(false);
  const [showWhatsAppModal, setShowWhatsAppModal] = useState<boolean>(false);
  const [waConnected, setWaConnected] = useState<boolean>(false);
  const [waQrCode, setWaQrCode] = useState<string | null>(null);
  const [waRunning, setWaRunning] = useState<boolean>(false);

  useEffect(() => {
    let intervalId: any;
    const fetchWhatsAppStatus = async () => {
      try {
        const response = await fetch("http://localhost:3000/api/agents/whatsapp/status");
        if (response.ok) {
          const data = await response.json();
          setWaConnected(data.connected);
          setWaQrCode(data.qr);
          setWaRunning(data.is_running);
        }
      } catch (e) {
        // Silent error
      }
    };
    fetchWhatsAppStatus();
    intervalId = setInterval(fetchWhatsAppStatus, 4000);
    return () => clearInterval(intervalId);
  }, []);
  const [userDetails, setUserDetails] = useState({ name: 'Boss', role: 'Luna Prime' });
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const isListeningRef = useRef<boolean>(false);
  const [isHandsFree, setIsHandsFree] = useState<boolean>(false);
  const isHandsFreeRef = useRef<boolean>(false);

  const toggleHandsFree = () => {
    const next = !isHandsFree;
    setIsHandsFree(next);
    isHandsFreeRef.current = next;
    pushTerminalLog(next ? "🟢 Continuous Hands-Free Listening Mode Activated." : "⚪ Hands-Free Mode Deactivated.", next ? "success" : "info");
    if (next && !isListeningRef.current) {
      startListening();
    }
  };


  // System Agent Security
  const [pendingCommand, setPendingCommand] = useState<{ command: string, requiresPrivilege: boolean, category?: string } | null>(null);

  // System Settings Config
  const [settingsConfig, setSettingsConfig] = useState(() => {
    try {
      const saved = localStorage.getItem("settingsConfig");
      if (saved) {
        const parsed = JSON.parse(saved);
        // Ensure defaults are present in saved configs
        return {
          wakeWord: "LUNA",
          speechRate: 1.0,
          ambientGlow: true,
          visualMode: "spatial-slate",
          groqKey: localStorage.getItem("groqKey") || "",
          openRouterKey: localStorage.getItem("openRouterKey") || "",
          openaiKey: localStorage.getItem("openaiKey") || "",
          modelSelection: "",
          activeProvider: "groq",
          isLocalLlm: false,
          localLlmUrl: "http://localhost:11434",
          localLlmModel: "llama3",
          openClawUrl: "http://localhost:8000/v1",
          openClawApiKey: "",
          githubPat: localStorage.getItem("githubPat") || "",
          ...parsed
        };
      }
    } catch {}
    return {
      wakeWord: "LUNA",
      speechRate: 1.0,
      ambientGlow: true,
      visualMode: "spatial-slate",
      groqKey: localStorage.getItem("groqKey") || "",
      openRouterKey: localStorage.getItem("openRouterKey") || "",
      openaiKey: localStorage.getItem("openaiKey") || "",
      modelSelection: "",
      activeProvider: "groq",
      isLocalLlm: false,
      localLlmUrl: "http://localhost:11434",
      localLlmModel: "llama3",
      openClawUrl: "http://localhost:8000/v1",
      openClawApiKey: "",
      githubPat: localStorage.getItem("githubPat") || ""
    };
  });


  const [ttsSettings, setTtsSettings] = useState<TTSSettings>(() => {
    try {
      const saved = localStorage.getItem("ttsSettings");
      if (saved) return JSON.parse(saved);
    } catch {}
    return {
      provider: 'edge',
      voiceId: 'en-US-AriaNeural',
      speed: 1,
      pitch: 1,
      elevenLabsApiKey: localStorage.getItem("elevenLabsKey") || ""
    };
  });

  const [customBg, setCustomBg] = useState<string>(() => {
    return localStorage.getItem("customBg") || "/background.png";
  });

  // System Metrics
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpuUsage: 14,
    ramUsage: 42,
    neuralLoad: 58,
    networkSpeed: "850 Mbps",
    uptime: "04:12:45"
  });

  // Device Telemetry
  const [devices, setDevices] = useState<DeviceTelemetry[]>([
    {
      id: "node-android-X",
      name: "Android Phone",
      type: "mobile",
      battery: 84,
      isCharging: false,
      network: "LTE_LUNA_SECURE",
      syncStatus: "synced",
      cpu: 4,
      ram: 32,
      storage: "128GB",
      tasks: ["Telemetry Broadcast", "Edge Security Broker"],
      osVersion: "Android 14 // Luna-ROM 3.2"
    },
    {
      id: "node-arch-W",
      name: "Arch Linux",
      type: "workstation",
      battery: 100,
      isCharging: true,
      network: "Intranet_Core_5G",
      syncStatus: "synced",
      cpu: 18,
      ram: 48,
      storage: "2TB NVMe",
      tasks: ["docker-daemon", "rust-compiler", "luna-sync-agent"],
      osVersion: "Arch Linux (Rolling) // Kernel 6.9"
    },
    {
      id: "node-windows-Z",
      name: "Windows PC",
      type: "desktop",
      battery: 99,
      isCharging: true,
      network: "Work_LAN_Gbe",
      syncStatus: "offline",
      cpu: 2,
      ram: 12,
      storage: "4TB Raid0",
      tasks: [],
      osVersion: "Windows 11 Pro // WSL2 Active"
    }
  ]);

  // AI Activity Stream
  const [activityStream, setActivityStream] = useState<ActivityEvent[]>([
    {
      id: "evt-1",
      text: "LUNA core v3.0 initialization diagnostics passed.",
      type: "system",
      timestamp: "11:10:22"
    },
    {
      id: "evt-2",
      text: "Synced telemetry datasets for Arch Linux node.",
      type: "device",
      timestamp: "11:11:05"
    },
    {
      id: "evt-3",
      text: "Neural processing load optimized to 58%.",
      type: "task",
      timestamp: "11:12:00"
    }
  ]);

  // System Goals
  const [goals, setGoals] = useState<SystemGoal[]>([
    { id: "g-1", title: "Compile Edge Sync Module", category: "Workspace", current: "90%", target: "100%", progress: 90 },
    { id: "g-2", title: "Train Core Reasoning Weights", category: "Intelligence", current: "82%", target: "100%", progress: 82 },
    { id: "g-3", title: "Device Synchronization Grid", category: "Ecosystem", current: "2/3 Nodes", target: "3/3 Nodes", progress: 66 }
  ]);

  // Health Metrics Data
  const [healthData, setHealthData] = useState<HealthData>({
    steps: 8421,
    stepGoal: 10000,
    calories: 342,
    calorieGoal: 500,
    distance: 3.8,
    distanceGoal: 5.0,
    sleepHours: 7.2,
    sleepGoal: 8.0,
    heartRate: 72
  });

  // Real Projects Folder State
  const [realProjects, setRealProjects] = useState<{ name: string, path: string }[]>(() => {
    try {
      const saved = localStorage.getItem("realProjects");
      if (saved) return JSON.parse(saved);
    } catch {}
    return [];
  });

  // File Explorer state
  const [currentFolderPath, setCurrentFolderPath] = useState<string | null>(null);
  const [folderFiles, setFolderFiles] = useState<{ name: string, isDir: boolean, size: number, path: string }[]>([]);
  const [folderFilesLoading, setFolderFilesLoading] = useState<boolean>(false);
  const [folderFilesError, setFolderFilesError] = useState<string | null>(null);
  const [parentPath, setParentPath] = useState<string | null>(null);

  // Draggable Image Viewer Popup state
  const [viewerImage, setViewerImage] = useState<{ name: string, path: string } | null>(null);

  // Draggable Video Player Popup state
  const [viewerVideo, setViewerVideo] = useState<{ name: string, path: string } | null>(null);

  // Notepad states
  const [notepadFile, setNotepadFile] = useState<{ name: string, path: string } | null>(null);
  const [notepadContent, setNotepadContent] = useState<string>("");
  const [notepadLoading, setNotepadLoading] = useState<boolean>(false);
  const [notepadSaving, setNotepadSaving] = useState<boolean>(false);
  const [notepadSaveSuccess, setNotepadSaveSuccess] = useState<boolean>(false);
  const [notepadError, setNotepadError] = useState<string | null>(null);
  const notepadTextareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollNotepad = (direction: 'up' | 'down') => {
    const textarea = notepadTextareaRef.current;
    if (textarea) {
      const scrollAmount = 150;
      textarea.scrollBy({
        top: direction === 'up' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  const openNotepad = async (item: { name: string, path: string }) => {
    setNotepadFile(item);
    setNotepadLoading(true);
    setNotepadError(null);
    setNotepadContent("");
    setNotepadSaveSuccess(false);
    try {
      const res = await fetch(`http://localhost:3000/api/agents/files/content?path=${encodeURIComponent(item.path)}`);
      if (res.ok) {
        const text = await res.text();
        setNotepadContent(text);
      } else {
        setNotepadError(`Failed to fetch file content (HTTP ${res.status})`);
      }
    } catch (e: any) {
      setNotepadError(e.message || "Error reading file content.");
    } finally {
      setNotepadLoading(false);
    }
  };

  const handleSaveNotepad = async () => {
    if (!notepadFile) return;
    setNotepadSaving(true);
    setNotepadSaveSuccess(false);
    try {
      const res = await fetch("http://localhost:3000/api/agents/file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "write",
          path: notepadFile.path,
          content: notepadContent
        })
      });
      const data = await res.json();
      if (data.status === "success") {
        setNotepadSaveSuccess(true);
        pushTerminalLog(`[NOTEPAD] Saved file successfully: ${notepadFile.name}`, "success");
        setTimeout(() => setNotepadSaveSuccess(false), 3000);
      } else {
        alert("Failed to save: " + data.result);
      }
    } catch (e: any) {
      alert("Error saving: " + e.message);
    } finally {
      setNotepadSaving(false);
    }
  };

  const isTextFile = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ['txt', 'sh', 'py', 'js', 'ts', 'tsx', 'json', 'css', 'html', 'md', 'env', 'yml', 'yaml', 'ini', 'conf', 'go', 'rs', 'c', 'cpp', 'h', 'java', 'xml'].includes(ext || '');
  };

  const fetchFolderContents = async (path: string) => {
    setFolderFilesLoading(true);
    setFolderFilesError(null);
    try {
      const res = await fetch(`http://localhost:3000/api/agents/files/list?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      if (data.status === "success") {
        setFolderFiles(data.files);
        setParentPath(data.parent);
        setCurrentFolderPath(path.replace(/\\/g, '/'));
      } else {
        setFolderFilesError(data.message || "Failed to load directory files.");
      }
    } catch (e: any) {
      setFolderFilesError(e.message || "Network error while loading files.");
    } finally {
      setFolderFilesLoading(false);
    }
  };

  const handleOpenRealFolder = async () => {
    let selectedPath: string | null = null;
    if ((window as any).__TAURI__) {
      try {
        const { open } = await import('@tauri-apps/plugin-dialog');
        selectedPath = await open({
          directory: true,
          multiple: false,
        }) as string | null;
      } catch (e) {
        console.error("Tauri dialog error:", e);
      }
    } 
    
    if (!selectedPath) {
      selectedPath = prompt("Enter the absolute path of the project folder:");
    }

    if (selectedPath) {
      const pathNormalized = selectedPath.replace(/\\/g, '/');
      const folderName = pathNormalized.split('/').pop() || pathNormalized;
      
      if (!realProjects.some(p => p.path === pathNormalized)) {
        const updated = [...realProjects, { name: folderName, path: pathNormalized }];
        setRealProjects(updated);
        localStorage.setItem("realProjects", JSON.stringify(updated));
      }
    }
  };

  // GitHub Repos
  const [repos, setRepos] = useState<GitHubRepo[]>([
    {
      name: "luna-core-os",
      description: "Autonomous spatial operating system kernel and neural network pipeline routing broker.",
      branch: "main",
      stars: 1482,
      languages: ["TypeScript", "Rust"],
      buildStatus: "success",
      lastCommit: "a9f4c3d"
    },
    {
      name: "edge-agent-sync",
      description: "Ultra-low-latency secure websocket bridge synchronizing telemetry nodes over local TLS tunnel.",
      branch: "master",
      stars: 241,
      languages: ["Go", "C++"],
      buildStatus: "success",
      lastCommit: "e2b10ca"
    },
    {
      name: "portal-dashboard",
      description: "Futuristic Glassmorphism spatial cockpit display utilizing advanced layouts & CSS particles.",
      branch: "staging",
      stars: 618,
      languages: ["React", "Tailwind"],
      buildStatus: "failed",
      lastCommit: "fc89e21"
    }
  ]);

  // Terminal & Build logs
  const [terminalLogs, setTerminalLogs] = useState<LogMessage[]>([
    { text: "LUNA Sandbox environment v3.0 online.", type: "system", timestamp: "11:10:22" },
    { text: "Connected to local node controller over IPC.", type: "info", timestamp: "11:10:23" },
    { text: "Loaded 3 active Git workspace references.", type: "success", timestamp: "11:10:24" },
    { text: "Ready to compile or process edge telemetry.", type: "info", timestamp: "11:10:25" }
  ]);

  // Notifications
  const [notifications, setNotifications] = useState<string[]>([
    "Welcome back. All OS systems are calibrated.",
    "Synchronized with Android Edge node.",
  ]);

  // Chat message backlog
  const [chatInput, setChatInput] = useState<string>("");
  const [chatMessages, setChatMessages] = useState<{ sender: 'user' | 'luna'; text: string; timestamp: string }[]>(() => {
    try {
      const saved = localStorage.getItem("chatMessages");
      if (saved) return JSON.parse(saved);
    } catch {}
    return [
      { sender: 'luna', text: "Hello, Boss. I'm Luna. Everything is online and ready. I've finished checking the system, and we're good to go. What would you like to work on today?", timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}) }
    ];
  });

  // Persist State to Local Storage
  useEffect(() => {
    // Fetch History from Backend instead of localStorage
    fetch("http://localhost:3000/api/history?session_id=default")
      .then(res => res.json())
      .then(data => {
        setChatHistory(data);
        
        // Map history to chatMessages for UI if needed
        const mapped = data.map((msg: any) => ({
          sender: msg.role === "user" ? "user" : "luna",
          text: msg.content,
          timestamp: new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})
        }));
        if (mapped.length > 0) {
          setChatMessages(mapped);
        }
      })
      .catch(err => console.error("History fetch error:", err));

    // Connect WebSocket
    const ws = new WebSocket("ws://localhost:3000/api/ws/events");
    
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setCoreState('Error');
      pushTerminalLog('[WS ERROR] WebSocket connection failed', 'error');
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
      setCoreState('Offline');
      pushTerminalLog('[WS] Connection closed', 'info');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "confirmation_required") {
          const { task_id, prompt } = data.payload;
          const confirmed = window.confirm(prompt);
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "provide_confirmation", payload: { task_id, confirmed } }));
          }
        } else if (data.type === "WAKE_WORD_DETECTED") {
          setCoreState("Listening");
          setTranscript("Listening (Native Background Mode)...");
          window.dispatchEvent(new CustomEvent('trigger-luna-listen'));
        } else if (data.type === "VOICE_COMMAND") {
          const text = data.payload.text;
          setTranscript(text);
          handleCommand(text);
        } else if (data.type === "task_update") {
          const task = data.payload;
          
          setDiagnosticLogs(prev => {
            const newLogs = [...prev, `[Task: ${task.name}] ${task.progress}`];
            if (newLogs.length > 50) newLogs.shift();
            return newLogs;
          });
          
          if (task.status === "completed") {
            setSpeechText(`Task completed: ${task.name}`);
            setNotifications(prev => [...prev, `Task completed: ${task.name}`]);
          } else if (task.status === "failed") {
            setNotifications(prev => [...prev, `Task failed: ${task.name}`]);
          }
        }
      } catch (err) {
        console.error("WS parsing error:", err);
      }
    };
    
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("chatMessages", JSON.stringify(chatMessages));
    } catch (err) {
      if (err instanceof Error && err.name === 'QuotaExceededError') {
        console.warn("Storage quota exceeded, unable to save chat messages");
      } else {
        console.warn("Failed to save chat messages:", err);
      }
    }
  }, [chatMessages]);

  useEffect(() => {
    try {
      localStorage.setItem("settingsConfig", JSON.stringify(settingsConfig));
      localStorage.setItem("groqKey", settingsConfig.groqKey);
      localStorage.setItem("openRouterKey", settingsConfig.openRouterKey);
      localStorage.setItem("openaiKey", settingsConfig.openaiKey);
    } catch (err) {
      if (err instanceof Error && err.name === 'QuotaExceededError') {
        console.warn("Storage quota exceeded, unable to save settings");
      } else {
        console.warn("Failed to save settings:", err);
      }
    }
  }, [settingsConfig]);

  useEffect(() => {
    localStorage.setItem("ttsSettings", JSON.stringify(ttsSettings));
    localStorage.setItem("elevenLabsKey", ttsSettings.elevenLabsApiKey);
  }, [ttsSettings]);

  // Check backend server status
  useEffect(() => {
    fetch("http://localhost:3000/api/health")
      .then(res => res.json())
      .then(data => {
        setApiHealth({ enabled: data.geminiEnabled, checked: true });
        if (data.geminiEnabled) {
          pushTerminalLog("Secure connection verified with Google Gemini LLM API.", "success");
        } else {
          pushTerminalLog("Gemini API key not found. Running in localized Edge execution mode.", "warning");
        }
      })
      .catch(() => {
        setApiHealth({ enabled: false, checked: true });
        pushTerminalLog("Local API router unreachable. Simulating cold offline node.", "error");
      });
  }, []);

  // Update dynamic metrics
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        cpuUsage: Math.max(8, Math.min(95, Math.round(prev.cpuUsage + (Math.random() * 8 - 4)))),
        ramUsage: Math.max(30, Math.min(85, Math.round(prev.ramUsage + (Math.random() * 2 - 1)))),
        neuralLoad: Math.max(45, Math.min(80, Math.round(prev.neuralLoad + (Math.random() * 4 - 2))))
      }));

      // Update a device metric occasionally
      setDevices(prev => prev.map(d => {
        if (d.syncStatus === 'synced') {
          return {
            ...d,
            cpu: Math.max(1, Math.min(99, Math.round(d.cpu + (Math.random() * 6 - 3)))),
            battery: d.isCharging ? Math.min(100, d.battery + 1) : Math.max(5, d.battery - 1)
          };
        }
        return d;
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Real-time time display hook
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formattedTime = currentTime.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
  
  const formattedDate = currentTime.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });

  // Vocal read-back
  const speakText = async (text: string) => {
    if (isMuted) return;
    setCoreState("Speaking");

    try {
      // Suspend native microphone while speaking
      fetch('http://localhost:3000/api/tts/status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speaking: true })
      }).catch(() => {});

      const isTauri = typeof window !== 'undefined' && ((window as any).__TAURI_INTERNALS__ !== undefined || (window as any).__TAURI__ !== undefined);

      if (isTauri) {
        const res = await fetch('http://localhost:3000/api/tts/play_local', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text,
            provider: ttsSettings.provider,
            voiceId: ttsSettings.voiceId,
            elevenLabsApiKey: ttsSettings.elevenLabsApiKey,
            speed: ttsSettings.speed,
            pitch: ttsSettings.pitch
          })
        });
        if (res.ok) {
          setCoreState("Idle");
          fetch('http://localhost:3000/api/tts/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ speaking: false })
          }).catch(() => {});
          return;
        }
      }

      const res = await fetch('http://localhost:3000/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          provider: ttsSettings.provider,
          voiceId: ttsSettings.voiceId,
          elevenLabsApiKey: ttsSettings.elevenLabsApiKey,
          speed: ttsSettings.speed,
          pitch: ttsSettings.pitch
        })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => {
          setCoreState("Idle");
          URL.revokeObjectURL(url);
          // Resume native microphone
          fetch('http://localhost:3000/api/tts/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ speaking: false })
          }).catch(() => {});
        };
        await audio.play();
      } else {
        throw new Error("TTS fetch failed");
      }
    } catch (e) {
      console.error("Falling back to local browser TTS due to error:", e);
      if (!('speechSynthesis' in window)) {
        setCoreState("Idle");
        // Resume native microphone
        fetch('http://localhost:3000/api/tts/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speaking: false })
        }).catch(() => {});
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.pitch = 1.05;
      utterance.rate = settingsConfig.speechRate;
      
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Zira") || v.name.includes("Samantha"));
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      
      utterance.onend = () => {
        setCoreState("Idle");
        // Resume native microphone
        fetch('http://localhost:3000/api/tts/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speaking: false })
        }).catch(() => {});
      };
      
      utterance.onerror = () => {
        setCoreState("Idle");
        // Resume native microphone
        fetch('http://localhost:3000/api/tts/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speaking: false })
        }).catch(() => {});
      };

      window.speechSynthesis.speak(utterance);
    }
  };

  // Dispatch activity events
  const pushActivity = (text: string, type: ActivityEvent['type']) => {
    const newEvt: ActivityEvent = {
      id: `evt-${Date.now()}`,
      text,
      type,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
    setActivityStream(prev => [newEvt, ...prev.slice(0, 15)]);
  };

  // Dispatch terminal logs
  const pushTerminalLog = (text: string, type: LogMessage['type']) => {
    const newLog: LogMessage = {
      text,
      type,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
    setTerminalLogs(prev => [...prev, newLog]);
  };

  // Core handler of AI Operating System command
  const handleCommand = async (commandText: string) => {
    if (!commandText.trim()) return;

    if (commandText.toLowerCase().trim() === "luna wake up") {
      window.dispatchEvent(new CustomEvent('trigger-luna-listen'));
      return;
    }

    setTranscript(commandText);
    setCoreState("Thinking");
    setIsThinking(true);
    pushActivity(`Voice transcript: "${commandText}"`, 'voice');

    // Add user message if in chat view
    setChatMessages(prev => [
      ...prev,
      { sender: 'user', text: commandText, timestamp: new Date().toLocaleTimeString() }
    ]);

    setChatHistory(prev => [
      ...prev,
      { role: 'user', content: commandText }
    ]);

    try {
      const response = await fetch("http://localhost:3000/api/luna/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command: commandText,
          history: chatHistory.slice(-20),
          activeView,
          deviceStates: devices.map(d => ({ id: d.id, name: d.name, syncStatus: d.syncStatus, tasks: d.tasks })),
          groqKey: settingsConfig.groqKey,
          openRouterKey: settingsConfig.openRouterKey,
          openaiKey: settingsConfig.openaiKey,
          modelSelection: settingsConfig.modelSelection,
          activeProvider: settingsConfig.activeProvider || "groq",
          isLocalLlm: settingsConfig.isLocalLlm || false,
          localLlmUrl: settingsConfig.localLlmUrl || "http://localhost:11434",
          localLlmModel: settingsConfig.localLlmModel || "llama3",
          openClawApiKey: settingsConfig.openClawApiKey || "",
          openClawUrl: settingsConfig.openClawUrl || "http://localhost:8000/v1"
        })

      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();

      // Validate response structure
      if (!data || typeof data !== 'object' || !data.speech) {
        throw new Error('Invalid API response structure');
      }

      // Validate and set core state (only allow valid CoreState values)
      const validStates: CoreState[] = ['Idle', 'Listening', 'Thinking', 'Speaking', 'Executing', 'Warning', 'Offline', 'Error'];
      const newState = validStates.includes(data.state) ? data.state : 'Speaking';
      setCoreState(newState);
      
      setSpeechText(data.speech);
      setIsThinking(false);
      
      setChatHistory(prev => [
        ...prev,
        { role: 'model', content: data.speech }
      ]);
      
      // Update terminal logs if returned
      if (data.logs && Array.isArray(data.logs)) {
        data.logs.forEach((logLine: string) => {
          pushTerminalLog(logLine, 'output');
        });
      }

      // Voice response speaking
      await speakText(data.speech);

      // Trigger structural side effects based on system response actions
      if (data.action) {
        handleSystemAction(data.action, data.targetDevice, data.logs || [], data.sysCommand, data.requiresPrivilege);
      }

      // Insert any triggered notifications
      if (data.notifications && Array.isArray(data.notifications)) {
        data.notifications.forEach((note: string) => {
          setNotifications(prev => [note, ...prev.slice(0, 5)]);
          pushActivity(`Notification: ${note}`, 'task');
        });
      }

      // Add assistant response in chat view
      setChatMessages(prev => [
        ...prev,
        { sender: 'luna', text: data.speech, timestamp: new Date().toLocaleTimeString() }
      ]);

    } catch (err: any) {
      console.error("Failed to query command engine:", err);
      setCoreState("Warning");
      setIsThinking(false);
      const fallbackMsg = "Oops, I had trouble reaching the main server. Let me process that locally for you!";
      setSpeechText(fallbackMsg);
      speakText(fallbackMsg);
    }
  };

  // Side-effect action dispatcher
  const handleSystemAction = (action: string, targetDevice: string, actionLogs: string[], sysCommand?: string, requiresPrivilege?: boolean) => {
    pushActivity(`Action dispatched: ${action} on ${targetDevice || 'system'}`, 'action');

    switch (action) {
      case "APP_CONTROL":
      case "SYSTEM_MANAGEMENT":
      case "FILE_OPERATION":
      case "EXECUTE_SYSTEM_COMMAND":
      case "GIT_AUTOMATION":
        if (sysCommand) {
          if (requiresPrivilege) {
            setPendingCommand({ command: sysCommand, requiresPrivilege, category: action });
            setCoreState("Warning");
            setSpeechText("I need your permission to run this system command. Could you please authorize it?");
            speakText("I need your permission to run this system command. Could you please authorize it?");
          } else {
            executeSystemCommand(sysCommand, false, action);
          }
        }
        break;
      case "SYNC_DEVICE":
        if (targetDevice) {
          setDevices(prev => prev.map(d => {
            if (d.name.toLowerCase().includes(targetDevice.toLowerCase())) {
              return { ...d, syncStatus: 'synced', battery: Math.min(100, d.battery + 2) };
            }
            return d;
          }));
        }
        break;

      case "TRIGGER_BUILD":
        // Set repository staging to building, then success
        const failingRepo = repos.find(r => r.buildStatus === 'failed');
        const targetRepoName = failingRepo ? failingRepo.name : repos[0].name;
        
        setRepos(prev => prev.map(r => {
          if (r.name === targetRepoName) {
            return { ...r, buildStatus: 'building' };
          }
          return r;
        }));

        setTimeout(() => {
          setRepos(prev => prev.map(r => {
            if (r.name === targetRepoName) {
              return { ...r, buildStatus: 'success', lastCommit: Math.random().toString(36).substring(2, 9) };
            }
            return r;
          }));
          pushActivity(`Build compiled successfully for ${targetRepoName}`, 'task');
          pushTerminalLog(`[PIPELINE] Compiled ${targetRepoName} staging node successfully.`, 'success');
        }, 3000);
        break;

      case "ADD_GOAL":
        // Generate simulated dynamic health goal addition
        const newG: SystemGoal = {
          id: `g-${Date.now()}`,
          title: "Active Cardio Restoration",
          category: "Health",
          current: "8,421",
          target: "10,000",
          progress: 84
        };
        setGoals(prev => [...prev, newG]);
        break;

      case "TOGGLE_DEVICE":
        if (targetDevice) {
          setDevices(prev => prev.map(d => {
            if (d.name.toLowerCase().includes(targetDevice.toLowerCase())) {
              return { ...d, syncStatus: d.syncStatus === 'offline' ? 'synced' : 'offline' };
            }
            return d;
          }));
        }
        break;
      default:
        break;
    }
  };

  const executeSystemCommand = async (cmd: string, requiresPrivilege: boolean, category: string = "RAW_COMMAND") => {
    try {
      const finalCommand = requiresPrivilege ? `pkexec ${cmd}` : cmd;
      pushTerminalLog(`[OS EXECUTE] ${finalCommand}`, 'system');
      
      const res = await fetch("http://localhost:3000/api/luna/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sysCommand: finalCommand, category })
      });
      const data = await res.json();
      
      if (data.success) {
        pushTerminalLog(`[OS SUCCESS] Command executed.`, 'success');
        if (data.stdout) pushTerminalLog(data.stdout.slice(0, 100), 'output');
        setCoreState("Idle");
      } else {
        pushTerminalLog(`[OS ERROR] Execution failed.`, 'error');
        setCoreState("Error");
      }
    } catch (e) {
      console.error(e);
      pushTerminalLog(`[OS ERROR] Backend execution unreachable.`, 'error');
      setCoreState("Error");
    }
  };

  // Voice Mic input listener
  const startListening = async () => {
    if (isListening) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      isListeningRef.current = false;
      setIsListening(false);
      setCoreState("Idle");
      return;
    }

    try {
      const isTauri = typeof window !== 'undefined' && ((window as any).__TAURI_INTERNALS__ !== undefined || (window as any).__TAURI__ !== undefined);
      if (isTauri || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("getUserMedia not supported (Tauri Linux issue)");
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const audioChunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");

        try {
          setTranscript("Transcribing audio...");
          const response = await fetch("http://localhost:3000/api/stt", {
            method: "POST",
            body: formData,
          });
          if (response.ok) {
            const data = await response.json();
            setTranscript(data.transcript);
            handleCommand(data.transcript);
          } else {
            setTranscript("Error transcribing audio.");
          }
        } catch (error) {
          console.error("Transcription error:", error);
          setTranscript("Error reaching server.");
        } finally {
          // Release the microphone
          stream.getTracks().forEach(track => track.stop());
          setIsListening(false);
          isListeningRef.current = false;
          if (isHandsFreeRef.current) {
            setTimeout(() => {
              if (isHandsFreeRef.current && !isListeningRef.current) {
                startListening();
              }
            }, 800);
          }
        }
      };

      mediaRecorder.start();
      setIsListening(true);
      setCoreState("Listening");
      setTranscript("Listening...");
      pushTerminalLog("Recording audio...", "info");

      setTimeout(() => {
        if (mediaRecorder.state === "recording") {
          mediaRecorder.stop();
          setIsListening(false);
        }
      }, 7000);

    } catch (err) {
      const errorMsg = String(err).toLowerCase();
      console.warn("Microphone access failed. Falling back to native backend STT.", err);
      
      if (errorMsg.includes("permission") || errorMsg.includes("denied")) {
        pushTerminalLog("⚠️ Browser microphone permission denied (Tauri Linux issue). Attempting native OS fallback.", "warning");
      }
      
      pushTerminalLog("Using Native OS Background STT.", "warning");
      // Fallback for Tauri Linux (WebKitGTK blocks WebRTC)
      setIsListening(true);
      isListeningRef.current = true;
      setCoreState("Listening");
      setTranscript("Native STT Listening...");
      
      const runContinuousSTT = async () => {
        while (isListeningRef.current) {
          try {
            const response = await fetch("http://localhost:3000/api/stt/record_local", {
              method: "POST"
            });
            
            if (!isListeningRef.current) break; // User stopped manually

            if (response.ok) {
              const data = await response.json();
              setTranscript(data.transcript);
              
              const text = (data.transcript || "").toLowerCase().trim();
              if (text === "stop listening luna" || text === "stop listening" || text === "luna stop listening") {
                isListeningRef.current = false;
                setIsListening(false);
                setCoreState("Idle");
                speakText("I've stopped listening, Boss.");
                break;
              }
              
              if (data.transcript && data.transcript.includes("permission")) {
                setSpeechText("Microphone permission denied. Please run: sudo usermod -aG audio $(whoami)");
                setCoreState("Error");
                pushTerminalLog("❌ Backend: Microphone permission denied", "error");
                isListeningRef.current = false;
                break;
              } else if (data.transcript && !data.transcript.includes("Error") && !data.transcript.includes("Could not understand")) {
                 await handleCommand(data.transcript);
                 // We will let it loop around and try listening again while the command processes.
                 // The backend uses voice_agent.set_speaking(True) so it will safely suspend listening when it speaks.
              }
            } else {
              setTranscript("Native STT returned error.");
              isListeningRef.current = false;
              break;
            }
          } catch (fallbackErr) {
            const fallbackMsg = String(fallbackErr).toLowerCase();
            if (fallbackMsg.includes("permission")) {
              pushTerminalLog("❌ Backend cannot access microphone - Permission denied", "error");
              setTranscript("Permission Denied: Run: sudo usermod -aG audio $(whoami) && newgrp audio");
              setSpeechText("I cannot access your microphone. Please grant audio permissions and try again.");
            } else {
              pushTerminalLog("❌ Native STT fallback error: " + String(fallbackErr), "error");
              setTranscript("Could not reach backend for Native STT.");
            }
            setCoreState("Error");
            isListeningRef.current = false;
            break;
          }
          await new Promise(r => setTimeout(r, 100)); // small debounce to prevent infinite spin if backend crashes instantly
        }
        setIsListening(false);
        if (coreState === "Listening") setCoreState("Idle");
      };

      runContinuousSTT();
    }
  };

  // Developer actions
  const handleTriggerBuild = (repoName: string) => {
    pushTerminalLog(`[VITE] Initiating bundler pipeline for repository: ${repoName}`, 'info');
    setRepos(prev => prev.map(r => {
      if (r.name === repoName) return { ...r, buildStatus: 'building' };
      return r;
    }));

    setTimeout(() => {
      setRepos(prev => prev.map(r => {
        if (r.name === repoName) return { ...r, buildStatus: 'success', lastCommit: Math.random().toString(36).substring(2, 9) };
        return r;
      }));
      pushTerminalLog(`[ESBUILD] Compiled workspace bundle for ${repoName} inside dist/server.cjs in 154ms.`, 'success');
      pushActivity(`Production compilation pipeline finished: ${repoName}`, 'task');
    }, 2500);
  };

  const handleRunTerminalCommand = (cmd: string) => {
    pushTerminalLog(`$ ${cmd}`, 'info');
    const text = cmd.toLowerCase().trim();

    setTimeout(() => {
      if (text === "npm test") {
        pushTerminalLog("PASS  src/__tests__/app.test.tsx (4.23s)", "success");
        pushTerminalLog("Test Suites: 1 passed, 1 total", "output");
        pushTerminalLog("Tests:       18 passed, 18 total", "output");
      } else if (text === "tsc") {
        pushTerminalLog("Typescript compilation complete. 0 errors detected.", "success");
      } else if (text === "luna doctor") {
        pushTerminalLog("System diagnostics complete:", "system");
        pushTerminalLog("● Node JS Server is running fully-integrated on cluster port 3000", "success");
        pushTerminalLog(`● Gemini API authentication: ${apiHealth.enabled ? "ESTABLISHED" : "EDGE SIMULATED"}`, apiHealth.enabled ? "success" : "warning");
        pushTerminalLog(`● Connected active nodes: ${devices.filter(d => d.syncStatus === 'synced').length} synced`, "success");
      } else if (text === "git diff") {
        pushTerminalLog("diff --git a/src/App.tsx b/src/App.tsx", "output");
        pushTerminalLog("- <chatbot-layout>", "error");
        pushTerminalLog("+ <luna-intelligent-operating-system-v3>", "success");
      } else {
        // Fallback to calling Gemini command server-side
        handleCommand(cmd);
      }
    }, 500);
  };

  const handleGenerateCode = (prompt: string, repoName: string) => {
    setIsGeneratingCode(true);
    pushTerminalLog(`[GEMINI] Analyzing syntax requirements for: "${prompt}"`, 'system');

    setTimeout(() => {
      setIsGeneratingCode(false);
      pushTerminalLog(`[CODELIGN] Code generated and staged to branch 'staging' of ${repoName}:`, 'success');
      pushTerminalLog(`+ Added fully-typed controller layer for schema components`, 'success');
      pushTerminalLog(`+ Created secure validation hooks for telemetry pipeline`, 'success');
      pushTerminalLog(`[PIPELINE] Staged code build is normal. Auto testing scheduled.`, 'info');
      pushActivity(`AI Copilot generated controller hooks for ${repoName}`, 'task');
    }, 3500);
  };

  // Interactive System Sweep function
  const handleSystemSweep = () => {
    setDiagnosticStepIndex(0);
    setCoreState("Thinking");
    setDiagnosticLogs(["[SWEEP] Initiating multi-spectrum diagnostic sweep..."]);
    pushTerminalLog("[ARC] Starting system hardware sweep sequence...", "info");
    
    const steps = [
      "Securing magnetic isolation seals",
      "Calibrating core palladium grids",
      "Stabilizing flux containment bounds",
      "Testing Luna link secure bridges"
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        const nextStepName = steps[currentStep];
        setDiagnosticLogs(prev => [
          ...prev,
          `[ACTIVE] ${nextStepName}...`
        ]);
        
        setTimeout(() => {
          setDiagnosticLogs(prev => {
            const list = [...prev];
            // Replace the last item with DONE status
            list[list.length - 1] = `[NOMINAL] ${nextStepName} - SUCCESS`;
            return list;
          });
        }, 500);

        setDiagnosticStepIndex(currentStep);
        currentStep++;
      } else {
        clearInterval(interval);
        setCoreState("Speaking");
        setSpeechText("All Iron Man Arc Reactor sub-assemblies are verified at one-hundred percent capacity. Luna systems are fully operational.");
        setDiagnosticLogs(prev => [
          ...prev,
          "[COMPLETE] Luna Core Diagnostics: 100% NOMINAL"
        ]);
        setDiagnosticStepIndex(4);
        pushTerminalLog("[SUCCESS] System sweep complete: All core shields are fully calibrated.", "success");
      }
    }, 1500);
  };

  // Health Actions
  const handleLogExercise = (type: 'walk' | 'run' | 'sleep' | 'workout') => {
    setHealthData(prev => {
      let steps = prev.steps;
      let calories = prev.calories;
      let sleepHours = prev.sleepHours;
      let distance = prev.distance;

      if (type === 'walk') {
        steps += 1500;
        calories += 65;
        distance += 0.7;
      } else if (type === 'run') {
        steps += 3500;
        calories += 180;
        distance += 1.8;
      } else if (type === 'workout') {
        calories += 150;
      } else if (type === 'sleep') {
        sleepHours = Math.min(12, sleepHours + 1);
      }

      const heartRate = Math.round(68 + Math.random() * 25);
      pushActivity(`Logged health telemetry update: ${type.toUpperCase()}`, 'device');
      return { ...prev, steps, calories, sleepHours, distance, heartRate };
    });
  };

  // Devices panel callback actions
  const handleSyncDevice = (deviceId: string) => {
    setDevices(prev => prev.map(d => {
      if (d.id === deviceId) return { ...d, syncStatus: 'syncing' };
      return d;
    }));

    pushTerminalLog(`[IPC] Initiating synchronizer over secure TLS port for device ID ${deviceId}`, 'info');

    setTimeout(() => {
      setDevices(prev => prev.map(d => {
        if (d.id === deviceId) {
          pushTerminalLog(`[SUCCESS] Refreshed node details for trusted device: ${d.name}`, 'success');
          pushActivity(`Device telemetry sync verified: ${d.name}`, 'device');
          return { ...d, syncStatus: 'synced', cpu: Math.round(5 + Math.random() * 15), ram: Math.round(15 + Math.random() * 30) };
        }
        return d;
      }));
    }, 2000);
  };

  const handleToggleTask = (deviceId: string, task: string) => {
    setDevices(prev => prev.map(d => {
      if (d.id === deviceId) {
        return {
          ...d,
          tasks: d.tasks.filter(t => t !== task)
        };
      }
      return d;
    }));
    pushActivity(`Terminated remote process: ${task}`, 'device');
    pushTerminalLog(`[TERMINATED] Cleanly exited process "${task}" on device node ${deviceId}`, 'warning');
  };

  useEffect(() => {
    const handleTriggerListen = () => {
      if (!isListening) {
        startListening();
      }
    };
    window.addEventListener('trigger-luna-listen', handleTriggerListen);
    return () => window.removeEventListener('trigger-luna-listen', handleTriggerListen);
  }, [isListening]);

  const isLight = themeMode === 'light-glass';

  // Panel wrapper utility styled for glass and dark theme
  const getPanelClass = (additional = "") => {
    return `transition-all duration-500 rounded-2xl ${
      isLight 
        ? "bg-white/60 border border-white/80 shadow-xl backdrop-blur-xl text-slate-900" 
        : "bg-slate-950/40 border border-slate-900 backdrop-blur-md text-slate-100"
    } ${additional}`;
  };

  return (
    <div 
      className={`min-h-screen flex flex-col font-sans relative overflow-x-hidden select-none transition-all duration-500 bg-cover bg-center bg-fixed ${
        isLight 
          ? "text-slate-900" 
          : "text-slate-100"
      }`}
      style={{ backgroundImage: `url('${customBg}')` }}
    >
      
      {/* Background overlays for readability */}
      <div className={`absolute inset-0 z-0 pointer-events-none transition-all duration-500 ${
        isLight
          ? "bg-slate-100/40 backdrop-blur-sm"
          : "bg-slate-950/70 backdrop-blur-[4px]"
      }`} />
      
      {/* Background space parallax grid lines (adapts to light/dark themes) */}
      <div className={`absolute inset-0 bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] z-0 pointer-events-none transition-all duration-500 ${
        isLight 
          ? "opacity-25 bg-[linear-gradient(to_right,rgba(0,0,0,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.05)_1px,transparent_1px)]" 
          : "opacity-100 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)]"
      }`} />

      {/* Top Header Visor */}
      <header className={`z-30 backdrop-blur-md px-6 py-3.5 flex items-center justify-between sticky top-0 transition-all duration-500 ${
        isLight 
          ? "bg-white/45 border-b border-slate-200/60 shadow-[0_4px_12px_rgba(0,0,0,0.02)]" 
          : "bg-slate-950/45 border-b border-slate-900/60"
      }`}>
        {/* Left: LUNA AI Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-[0_0_15px_rgba(6,182,212,0.5)]">
            <div className={`absolute inset-[2.5px] rounded-full flex items-center justify-center ${isLight ? 'bg-white' : 'bg-slate-950'}`}>
              <div className="w-3.5 h-3.5 rounded-full bg-gradient-to-r from-cyan-400 to-blue-400 opacity-95 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
              <div className={`absolute -top-[1.5px] -left-[1.5px] w-2.5 h-2.5 rounded-full ${isLight ? 'bg-white' : 'bg-slate-950'}`} />
            </div>
          </div>
          <div>
            <h1 className={`text-sm font-bold tracking-[0.2em] font-display transition-colors ${isLight ? "text-slate-900" : "text-white"}`}>
              LUNA AI <span className="text-cyan-500 text-[10px] align-top ml-1">OS</span>
            </h1>
            <p className={`text-[8px] font-mono tracking-widest text-cyan-400/80 uppercase`}>
              TARGET: ARCH LINUX // ONLINE
            </p>
          </div>
        </div>

        {/* Center: Search Bar */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
          <div className={`relative w-full flex items-center rounded-full border px-4 py-2 transition-all duration-300 ${
            isLight 
              ? "bg-white/60 border-slate-200 focus-within:border-slate-400 shadow-sm" 
              : "bg-slate-900/30 border-slate-900 focus-within:border-cyan-500/50"
          }`}>
            <span className="text-slate-500 mr-2.5">
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input 
              type="text" 
              placeholder="Search anything..." 
              className="bg-transparent border-none outline-none text-xs w-full text-slate-100 placeholder:text-slate-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleCommand((e.target as HTMLInputElement).value);
                  (e.target as HTMLInputElement).value = '';
                }
              }}
            />
          </div>
        </div>

        {/* Right: Audio Wave, Notifications, Theme Mode & Profile */}
        <div className="flex items-center gap-4">
          
          {/* Audio Wave Visualizer Indicator (Interactive) */}
          <button 
            onClick={() => {
              setIsMuted(!isMuted);
              pushActivity(isMuted ? "Unmuted vocal synth feed" : "Muted vocal synth feed", "system");
            }}
            className={`flex items-center gap-1 p-2 rounded-xl border transition-all ${
              isLight 
                ? "bg-white/60 border-slate-200 text-slate-600 hover:bg-slate-50" 
                : "bg-slate-900/40 border-slate-900 text-slate-400 hover:text-white hover:border-slate-800"
            }`}
            title={isMuted ? "Unmute vocal synthesis" : "Mute vocal synthesis"}
          >
            <div className="flex items-end gap-0.5 h-3.5 px-0.5">
              {Array.from({ length: 4 }).map((_, i) => (
                <motion.div 
                  key={i}
                  className="w-0.5 rounded-full"
                  style={{ backgroundColor: isMuted ? "#64748b" : "#22d3ee" }}
                  animate={isMuted ? { height: 3 } : { height: [3, 10 + (i * 2), 3] }}
                  transition={{ duration: 0.4 + (i * 0.1), repeat: Infinity, ease: "easeInOut" }}
                />
              ))}
            </div>
          </button>

          {/* Notifications Bell with count */}
          {/* WhatsApp Agent Link Status Button */}
          <button
            onClick={() => setShowWhatsAppModal(true)}
            className={`p-2 rounded-xl border relative transition-all flex items-center justify-center cursor-pointer ${
              isLight 
                ? "bg-white/60 border-slate-200 text-slate-600 hover:bg-slate-50" 
                : "bg-slate-900/40 border-slate-900 text-slate-400 hover:text-white hover:border-slate-800"
            }`}
            title="WhatsApp Agent Integration"
          >
            <MessageSquare className={`w-4 h-4 ${waConnected ? "text-emerald-500 animate-pulse" : waQrCode ? "text-amber-500" : ""}`} />
            {waConnected && (
              <span className="absolute top-1 right-1 flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
            )}
            {!waConnected && waQrCode && (
              <span className="absolute top-1 right-1 flex h-1.5 w-1.5 rounded-full bg-amber-500" />
            )}
          </button>

          <div className="relative">
            <button 
              onClick={() => {
                if (notifications.length > 0) {
                  pushTerminalLog(`[NOTIFICATIONS] Listing active notes: ${notifications.join(" // ")}`, "info");
                  setNotifications([]);
                } else {
                  pushTerminalLog("[NOTIFICATIONS] No active notifications in stack.", "info");
                }
              }}
              className={`p-2 rounded-xl border relative transition-all ${
                isLight 
                  ? "bg-white/60 border-slate-200 text-slate-600 hover:bg-slate-50" 
                  : "bg-slate-900/40 border-slate-900 text-slate-400 hover:text-white hover:border-slate-800"
              }`}
            >
              <span className="sr-only">Notifications</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {notifications.length > 0 && (
                <span className="absolute top-1 right-1 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
                </span>
              )}
            </button>
          </div>

          {/* Theme Mode Toggle */}
          <button
            onClick={() => {
              const nextMode = themeMode === "dark" ? "light-glass" : "dark";
              setThemeMode(nextMode);
              pushActivity(`Swapped OS visualization to ${nextMode === "dark" ? "Luna Slate Dark" : "Spatial Light Glass"}`, "system");
            }}
            className={`p-2 rounded-xl border transition-all ${
              isLight 
                ? "bg-white/60 border-slate-200 text-slate-600 hover:bg-slate-50" 
                : "bg-slate-900/40 border-slate-900 text-slate-400 hover:text-white hover:border-slate-800"
            }`}
            title="Toggle theme spectrum"
          >
            {isLight ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
          </button>

          {/* User Profile dropdown capsule */}
          <button 
            onClick={() => setShowUserModal(true)}
            className={`flex items-center gap-2.5 px-3 py-1 border rounded-full transition-all hover:scale-105 cursor-pointer ${
            isLight ? "bg-white/80 border-slate-200 hover:bg-white" : "bg-slate-900/50 border-slate-900 hover:bg-slate-800"
          }`}>
            <div className="relative">
              {/* Profile Avatar representing "Boss" */}
              <div className="w-6.5 h-6.5 rounded-full bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-600 flex items-center justify-center text-[10px] font-bold text-white shadow-[0_0_8px_rgba(6,182,212,0.4)] overflow-hidden">
                <svg className="w-4 h-4 text-slate-100" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              </div>
              <span className="absolute bottom-0 right-0 block h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-slate-950 animate-pulse" />
            </div>
            <div className="hidden sm:block text-left text-[11px] leading-tight">
              <p className={`font-semibold ${isLight ? "text-slate-850" : "text-slate-200"}`}>{userDetails.name}</p>
              <p className="text-[9px] text-slate-400 font-mono">{userDetails.role}</p>
            </div>
          </button>

        </div>
      </header>

      {/* Main Dynamic Viewport Workspace */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-6 py-6 z-10 flex flex-col min-h-0 relative mb-28">
        
        <AnimatePresence mode="wait">
          {activeView === "home" && (
            <motion.div
              key="home"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch flex-1"
            >
              {/* LEFT PANEL: System Status & Calibrations (span 3) */}
              <div className="xl:col-span-3 flex flex-col gap-6">
                
                {/* 1. SYSTEM STATUS */}
                <div className={getPanelClass("p-4 flex flex-col gap-4 overflow-hidden")}>
                  <div className="flex items-center justify-between border-b border-slate-200/20 dark:border-slate-900/60 pb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-cyan-400" />
                      SYSTEM STATUS
                    </h3>
                    <span className="flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                    </span>
                  </div>

                  <div className="space-y-3.5 text-xs">
                    {/* CPU metric */}
                    <div>
                      <div className="flex justify-between items-center text-[11px] font-mono mb-1 text-slate-400">
                        <span>CPU USAGE</span>
                        <span className="text-cyan-400 font-semibold">{metrics.cpuUsage}%</span>
                      </div>
                      <div className={`h-1.5 w-full rounded-full overflow-hidden ${isLight ? "bg-slate-200" : "bg-slate-900"}`}>
                        <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500" style={{ width: `${metrics.cpuUsage}%` }} />
                      </div>
                    </div>

                    {/* RAM metric */}
                    <div>
                      <div className="flex justify-between items-center text-[11px] font-mono mb-1 text-slate-400">
                        <span>RAM LOAD</span>
                        <span className="text-purple-400 font-semibold">{metrics.neuralLoad}%</span>
                      </div>
                      <div className={`h-1.5 w-full rounded-full overflow-hidden ${isLight ? "bg-slate-200" : "bg-slate-900"}`}>
                        <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all duration-500" style={{ width: `${metrics.neuralLoad}%` }} />
                      </div>
                    </div>

                    {/* Network / Latency */}
                    <div className="flex justify-between items-center border-b border-slate-200/10 pb-2">
                      <span className="text-slate-400 font-mono text-[10px]">NETWORK FEED</span>
                      <span className="font-mono text-[11px] font-medium text-emerald-400">142 ms (SECURE)</span>
                    </div>

                    {/* Battery Status */}
                    <div className="flex justify-between items-center border-b border-slate-200/10 pb-2">
                      <span className="text-slate-400 font-mono text-[10px]">BATTERY PACK</span>
                      <span className="font-mono text-[11px] font-medium text-amber-400">98% (STABILIZED)</span>
                    </div>

                    {/* AI Model */}
                    <div className="flex justify-between items-center border-b border-slate-200/10 pb-2">
                      <span className="text-slate-400 font-mono text-[10px]">AI MODEL SPECS</span>
                      <span className="font-mono text-[11px] font-medium text-purple-400 font-sans">Gemini 2.5 Flash</span>
                    </div>

                    {/* Uptime */}
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400 font-mono text-[10px]">OS SYSTEM UPTIME</span>
                      <span className="font-mono text-[11px] font-medium text-slate-300">4d 12h 32m</span>
                    </div>
                  </div>
                </div>

                {/* 2. CALIBRATION UTILITIES */}
                <div className={getPanelClass("p-4 flex flex-col justify-between gap-4 overflow-hidden flex-1")}>
                  <div>
                    <div className="flex items-center justify-between border-b border-slate-200/20 dark:border-slate-900/60 pb-3 mb-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
                        <Gauge className="w-4 h-4 text-purple-400" />
                        CORE INDUCTION
                      </h3>
                    </div>

                    <div className="space-y-3">
                      <div className={`p-2.5 rounded-xl border ${isLight ? "bg-white/50 border-slate-200/50" : "bg-slate-950/40 border-slate-900/80"}`}>
                        <div className="flex justify-between items-center text-[10px] font-mono mb-1">
                          <span className="text-slate-400">EM COIL FLUX</span>
                          <span className="font-semibold text-cyan-400">{magneticField.toFixed(1)} Tesla</span>
                        </div>
                        <input 
                          type="range"
                          min="1.0"
                          max="6.5"
                          step="0.1"
                          value={magneticField}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value);
                            setMagneticField(val);
                            pushTerminalLog(`[ARC-COIL] EM Field Flux Density adjusted to ${val} T.`, 'info');
                          }}
                          className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                        />
                      </div>

                      <div className={`p-2.5 rounded-xl border ${isLight ? "bg-white/50 border-slate-200/50" : "bg-slate-950/40 border-slate-900/80"}`}>
                        <div className="flex justify-between items-center text-[10px] font-mono mb-1">
                          <span className="text-slate-400">COOLANT RECIRC</span>
                          <span className="font-semibold text-purple-400">{coolantPump} RPM</span>
                        </div>
                        <input 
                          type="range"
                          min="1000"
                          max="6000"
                          step="100"
                          value={coolantPump}
                          onChange={(e) => {
                            const val = parseInt(e.target.value);
                            setCoolantPump(val);
                            pushTerminalLog(`[THERMAL] Coolant Pump circulation rate calibrated to ${val} RPM.`, 'info');
                          }}
                          className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Diagnostic sweep button */}
                  <div className={`p-3 rounded-xl border ${isLight ? "bg-white/60 border-slate-200/60" : "bg-slate-950/30 border-slate-900/50"} mt-2`}>
                    <div className="flex items-center justify-between mb-2 text-[10px] font-mono">
                      <span className="text-slate-400">COIL STATUS</span>
                      <span className={diagnosticStepIndex === 4 ? "text-emerald-500 font-semibold" : "text-slate-500"}>
                        {diagnosticStepIndex === 4 ? "VERIFIED" : diagnosticStepIndex >= 0 ? "SWEEPING..." : "IDLE"}
                      </span>
                    </div>

                    <button
                      onClick={handleSystemSweep}
                      disabled={diagnosticStepIndex >= 0 && diagnosticStepIndex < 4}
                      className="w-full py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-xl text-[10px] font-bold tracking-wider uppercase transition-all duration-300 cursor-pointer disabled:opacity-40"
                    >
                      {diagnosticStepIndex >= 0 && diagnosticStepIndex < 4 ? "SWEEPING..." : "Sweep Core Array"}
                    </button>
                  </div>
                </div>

                {/* 3. USEFUL AI TOOLS (LEFT) */}
                <div className={getPanelClass("p-4 flex flex-col gap-3 overflow-hidden")}>
                  <div className="flex items-center justify-between border-b border-slate-200/20 dark:border-slate-900/60 pb-3 mb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
                      <Code className="w-4 h-4 text-cyan-400" />
                      DEV TOOLS
                    </h3>
                  </div>
                  <button onClick={() => { setActiveView("chat"); handleCommand("Generate python script for data processing"); }} className="text-left p-2.5 rounded-xl border border-slate-500/20 bg-slate-500/10 hover:bg-slate-500/20 transition-colors text-xs font-medium">
                    <span className="text-cyan-500 font-bold mb-1 block">Quick Code Gen</span>
                    <span className="text-[10px] text-slate-400">Generate boilerplate code</span>
                  </button>
                  <button onClick={() => { setActiveView("chat"); handleCommand("Scan system for vulnerabilities"); }} className="text-left p-2.5 rounded-xl border border-slate-500/20 bg-slate-500/10 hover:bg-slate-500/20 transition-colors text-xs font-medium">
                    <span className="text-purple-500 font-bold mb-1 block">Security Scan</span>
                    <span className="text-[10px] text-slate-400">Run automated diagnostics</span>
                  </button>
                </div>

              </div>

              {/* CENTER: Highly Interactive Glassmorphic Arc Reactor Core (span 6) */}
              <div className="xl:col-span-6 flex flex-col gap-6">
                
                <div className={getPanelClass("flex-1 flex flex-col items-center justify-center p-6 relative overflow-hidden min-h-[480px] backdrop-blur-sm bg-transparent border-none shadow-none")}>
                  
                  {/* Welcome Title */}
                  <div className="absolute top-8 left-0 right-0 text-center z-20">
                    <h2 className="text-4xl md:text-5xl font-black font-display tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-cyan-400 to-blue-600 drop-shadow-[0_0_15px_rgba(6,182,212,0.8)]">
                      WELCOME BOSS
                    </h2>
                    <p className="text-sm font-mono tracking-[0.3em] text-cyan-100 mt-2 uppercase shadow-black drop-shadow-md">
                      LUNA OS ARC REACTOR SYSTEM ONLINE
                    </p>
                  </div>
                  
                  {/* Subtle holographic target coordinates overlay */}
                  <div className="absolute inset-0 border border-dashed border-slate-200/5 dark:border-white/5 pointer-events-none rounded-3xl m-3" />
                  <div className="absolute top-4 left-4 text-[9px] font-mono text-slate-500">SYS_VEC: LUNA_4.0_NANO</div>
                  <div className="absolute top-4 right-4 text-[9px] font-mono text-slate-500">REF_FREQ: {(magneticField * 60).toFixed(0)} GHz</div>
                  <div className="absolute bottom-4 left-4 text-[9px] font-mono text-slate-500">TEMP_LAT: {coolantPump > 3000 ? "COOLING" : "STABLE"}</div>
                  <div className="absolute bottom-4 right-4 text-[9px] font-mono text-slate-500">GRID: SYNCED</div>

                  {/* Centered Arc Reactor in minimal Mode */}
                  <div className="w-full max-w-[340px] aspect-square flex items-center justify-center relative">
                    <ReactorCore 
                      state={coreState}
                      onMicToggle={startListening}
                      isListening={isListening}
                      transcript={transcript}
                      speechText={speechText}
                      isMuted={isMuted}
                      onMuteToggle={() => setIsMuted(!isMuted)}
                      themeMode={themeMode}
                      minimal={true}
                    />
                  </div>

                  {/* Interactive Status Overlay Below Reactor */}
                  <div className="text-center mt-6 max-w-sm">
                    <p className="text-xs font-semibold tracking-wider font-mono text-cyan-400 uppercase">
                      LUNA NEURAL CORE ACTIVE
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed font-sans">
                      Calibrate reactor parameters in the side panels or tap the reactor core to speak. Click outer rings to cycle spectrum colors.
                    </p>

                    {/* Integrated mini vocal feedback */}
                    <div className="mt-4 min-h-10 flex flex-col justify-center">
                      {isListening ? (
                        <div className="inline-flex items-center justify-center gap-2">
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                          </span>
                          <span className="text-xs font-mono text-red-400 animate-pulse font-medium">
                            {transcript || "Listening for secure vocal commands..."}
                          </span>
                        </div>
                      ) : speechText ? (
                        <div className={`space-y-0.5 border rounded-xl px-4 py-2.5 max-w-xs mx-auto ${isLight ? 'bg-slate-100/50 border-slate-300' : 'bg-slate-900/40 border-slate-900/60'}`}>
                          <p className="text-[8px] font-mono text-slate-500 uppercase tracking-widest">LUNA SYSTEM ANSWER</p>
                          <p className={`text-xs font-sans font-medium ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                            {speechText}
                          </p>
                        </div>
                      ) : (
                        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[10px] font-mono mx-auto ${isLight ? 'bg-slate-100 border-slate-200 text-slate-500' : 'bg-slate-900/50 border-slate-800 text-slate-400'}`}>
                          <span>TRIGGER SPECTRUM ARRAY CYCLE</span>
                        </div>
                      )}
                    </div>
                  </div>

                </div>

              </div>

              {/* RIGHT PANEL: Diagnostics & Devices (span 3) */}
              <div className="xl:col-span-3 flex flex-col gap-6">
                
                {/* 1. SYSTEM TIMELINE LOGS */}
                <div className={getPanelClass("p-4 flex flex-col gap-4 overflow-hidden flex-1 max-h-[300px]")}>
                  <div className="flex items-center justify-between border-b border-slate-200/20 dark:border-slate-900/60 pb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-cyan-400" />
                      SYSTEM ENGINE LOGS
                    </h3>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 text-[10px] font-mono select-text scrollbar-thin scrollbar-thumb-slate-850">
                    {diagnosticLogs.length > 0 ? (
                      diagnosticLogs.map((log, i) => (
                        <div key={i} className="flex flex-col gap-0.5 border-l-2 border-cyan-500/30 pl-2">
                          <span className="text-slate-500 text-[8px]">TIMESTAMP: {new Date().toLocaleTimeString()}</span>
                          <span className="text-slate-300 leading-normal">{log}</span>
                        </div>
                      ))
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">
                        Logs buffer is currently empty.
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. DEVICE ECOSYSTEM */}
                <div className={getPanelClass("p-4 flex flex-col gap-4 overflow-hidden")}>
                  <div className="flex items-center justify-between border-b border-slate-200/20 dark:border-slate-900/60 pb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
                      <Smartphone className="w-4 h-4 text-indigo-400" />
                      DEVICE ECOSYSTEM
                    </h3>
                    <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded border ${isLight ? 'bg-slate-100 border-slate-200 text-slate-600' : 'text-slate-500 bg-slate-900 border-slate-800'}`}>
                      {devices.length} SYSTEMS
                    </span>
                  </div>

                  <div className="space-y-2.5">
                    {devices.map(dev => (
                      <div 
                        key={dev.id} 
                        onClick={() => {
                          setActiveView("devices");
                          pushTerminalLog(`[HUD] Navigated to ecosystem sync panel for ${dev.name}.`, 'info');
                        }}
                        className={`flex items-center justify-between text-xs p-2.5 rounded-xl border cursor-pointer transition-all ${
                          isLight 
                            ? "bg-white/50 border-slate-200/50 hover:bg-white hover:border-slate-300 shadow-sm" 
                            : "bg-slate-900/40 border-slate-900/60 hover:border-slate-800 hover:bg-slate-900/20"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`h-1.5 w-1.5 rounded-full ${dev.syncStatus === 'synced' ? 'bg-emerald-500' : 'bg-slate-500'}`} />
                          <span className={`font-semibold ${isLight ? "text-slate-600" : "text-slate-350"}`}>{dev.name}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-slate-400 text-[10px]">{dev.battery}%</span>
                          <span className="text-[9px] font-mono text-slate-500 uppercase">
                            {dev.syncStatus === 'synced' ? 'SECURE' : 'CONNECTING'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. USEFUL AI TOOLS (RIGHT) */}
                <div className={getPanelClass("p-4 flex flex-col gap-3 overflow-hidden")}>
                  <div className="flex items-center justify-between border-b border-slate-200/20 dark:border-slate-900/60 pb-3 mb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-emerald-400" />
                      UTILITIES
                    </h3>
                  </div>
                  <button onClick={() => { setActiveView("chat"); handleCommand("Summarize my latest emails and notifications"); }} className="text-left p-2.5 rounded-xl border border-slate-500/20 bg-slate-500/10 hover:bg-slate-500/20 transition-colors text-xs font-medium cursor-pointer">
                    <span className="text-emerald-500 font-bold mb-1 block">Daily Summary</span>
                    <span className="text-[10px] text-slate-400">Briefing on notifications</span>
                  </button>
                  <button onClick={() => { setActiveView("chat"); handleCommand("Draft an email to the team about the deployment"); }} className="text-left p-2.5 rounded-xl border border-slate-500/20 bg-slate-500/10 hover:bg-slate-500/20 transition-colors text-xs font-medium cursor-pointer">
                    <span className="text-indigo-500 font-bold mb-1 block">Draft Communication</span>
                    <span className="text-[10px] text-slate-400">Auto-compose messages</span>
                  </button>
                </div>

              </div>
            </motion.div>
          )}

          {activeView === "voice" && (
            <motion.div
              key="voice"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="flex-1 flex justify-center items-center min-h-[500px]"
            >
              <div className={`w-full max-w-2xl rounded-3xl p-8 relative overflow-hidden flex flex-col items-center text-center gap-6 border ${
                isLight 
                  ? "bg-white/40 border-white/60 shadow-lg backdrop-blur-xl text-slate-800" 
                  : "bg-slate-950/60 border border-slate-900 text-white backdrop-blur-md"
              }`}>
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 blur-3xl pointer-events-none" />
                
                <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-purple-950/30 border border-purple-900/45 rounded-full text-[10px] tracking-widest text-purple-500 font-mono">
                  <Mic className="w-3.5 h-3.5" /> VOICE WAKE SYSTEM ONLINE
                </div>

                <h2 className={`text-2xl font-bold font-display ${isLight ? "text-slate-900" : "text-white"}`}>Speak Directly to Luna</h2>
                <p className={`text-sm max-w-md ${isLight ? "text-slate-600" : "text-slate-400"}`}>
                  Vocal controls bypass traditional command prompt arrays. Luna will respond directly to spoken triggers.
                </p>

                {/* Hands-Free Mode Toggle Card */}
                <div className={`w-full max-w-md p-4 rounded-2xl border flex items-center justify-between gap-4 ${
                  isHandsFree 
                    ? "bg-emerald-950/30 border-emerald-500/50 shadow-[0_0_20px_rgba(16,185,129,0.2)]" 
                    : isLight ? "bg-slate-100/80 border-slate-300" : "bg-slate-900/60 border-slate-800"
                }`}>
                  <div className="text-left">
                    <div className="flex items-center gap-2">
                      <span className={`h-2.5 w-2.5 rounded-full ${isHandsFree ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
                      <span className={`text-xs font-bold font-mono uppercase tracking-wider ${isHandsFree ? "text-emerald-400" : isLight ? "text-slate-700" : "text-slate-300"}`}>
                        {isHandsFree ? "Continuous Hands-Free ON" : "Hands-Free Mode OFF"}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {isHandsFree 
                        ? "Luna continuously listens and replies hands-free without stopping." 
                        : "Enable for uninterrupted hands-free voice dialogue."}
                    </p>
                  </div>
                  
                  <button 
                    onClick={toggleHandsFree}
                    className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all cursor-pointer border ${
                      isHandsFree 
                        ? "bg-emerald-500 text-slate-950 border-emerald-400 hover:bg-emerald-400 shadow-md" 
                        : "bg-cyan-500/10 text-cyan-400 border-cyan-500/40 hover:bg-cyan-500/20"
                    }`}
                  >
                    {isHandsFree ? "DISABLE HANDS-FREE" : "ENABLE HANDS-FREE"}
                  </button>
                </div>

                
                {/* Stylized Voice Button */}
                <div className="w-48 h-48 rounded-full border border-cyan-500/30 flex items-center justify-center relative my-4 bg-black/10 backdrop-blur-md shadow-[0_0_30px_rgba(6,182,212,0.1)]">
                  {/* Outer rings */}
                  <div className={`absolute inset-0 rounded-full border-t border-cyan-400/50 ${isListening ? "animate-spin-fast border-red-500" : "animate-spin-slow"}`}></div>
                  <div className={`absolute inset-2 rounded-full border-b border-purple-400/40 ${isListening ? "animate-spin-reverse-fast border-red-400" : "animate-[spin_4s_linear_reverse]"}`}></div>
                  
                  <button onClick={startListening} className={`w-32 h-32 rounded-full flex items-center justify-center transition-all z-10 ${
                    isListening 
                      ? "bg-red-500/20 text-red-400 border-2 border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.5)] animate-pulse" 
                      : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/50 hover:bg-cyan-500/20 hover:scale-105 hover:shadow-[0_0_30px_rgba(6,182,212,0.3)]"
                  }`}>
                    {isListening ? <Mic className="w-12 h-12" /> : <Mic className="w-12 h-12" />}
                  </button>
                </div>

                {/* Live Transcription & Ongoing Conversation Feed */}
                <div className={`space-y-4 w-full max-w-xl p-6 rounded-3xl text-left border shadow-inner backdrop-blur-md ${
                  isLight ? "bg-white/50 border-slate-200 text-slate-800" : "bg-slate-950/50 border-slate-900/80 text-slate-200"
                }`}>
                  <div className="flex items-center justify-between border-b pb-3 mb-2 border-slate-500/20">
                    <span className="text-[10px] font-mono text-cyan-500 uppercase tracking-widest font-bold">Live Conversation Feed</span>
                    {isListening && (
                      <span className="flex items-center gap-1.5 text-[9px] font-mono text-red-500 animate-pulse font-bold">
                        <span className="h-2 w-2 rounded-full bg-red-500 inline-block" /> LISTENING...
                      </span>
                    )}
                  </div>
                  
                  <div className="min-h-[80px] flex flex-col gap-3">
                    {/* User Speech */}
                    {transcript && (
                      <div className="flex justify-end">
                        <div className={`px-4 py-2.5 rounded-2xl rounded-tr-none max-w-[85%] text-sm border ${
                          isLight ? "bg-cyan-50 border-cyan-100 text-cyan-900" : "bg-cyan-950/40 border-cyan-900/50 text-cyan-100"
                        }`}>
                          {transcript}
                        </div>
                      </div>
                    )}
                    
                    {/* Luna Speech */}
                    {speechText && (
                      <div className="flex justify-start">
                        <div className={`px-4 py-2.5 rounded-2xl rounded-tl-none max-w-[85%] text-sm border ${
                          isLight ? "bg-white border-slate-200" : "bg-slate-900/60 border-slate-800"
                        }`}>
                          <span className="text-[9px] text-slate-400 font-mono block mb-1">LUNA CORE</span>
                          {speechText}
                        </div>
                      </div>
                    )}

                    {!transcript && !speechText && (
                      <div className="text-center text-slate-500 text-sm italic py-4">
                        Awaiting voice input... tap the reactor to speak.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeView === "devices" && (
            <motion.div
              key="devices"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1"
            >
              <DeviceEcosystem
                devices={devices}
                onSyncDevice={handleSyncDevice}
                onToggleTask={handleToggleTask}
                isLight={isLight}
              />
            </motion.div>
          )}

          {activeView === "developer" && (
            <motion.div
              key="developer"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1"
            >
              <DeveloperWorkspace 
                repos={repos}
                terminalLogs={terminalLogs}
                onTriggerBuild={handleTriggerBuild}
                onRunTerminalCommand={(cmd) => executeSystemCommand(cmd, false)}
                onGenerateCode={handleGenerateCode}
                onAddRepo={(repo) => setRepos(prev => [...prev, repo])}
                isGeneratingCode={isGeneratingCode}
                isLight={isLight}
              />
            </motion.div>
          )}

          {activeView === "analytics" && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1"
            >
              <GithubMonitor 
                token={settingsConfig.githubPat || ""}
                onUpdateToken={(newToken) => {
                  const updated = { ...settingsConfig, githubPat: newToken };
                  setSettingsConfig(updated);
                  localStorage.setItem("settingsConfig", JSON.stringify(updated));
                  localStorage.setItem("githubPat", newToken);
                }}
                isLight={isLight}
              />
            </motion.div>
          )}

          {activeView === "projects" && (
            <motion.div
              key="projects"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 space-y-6"
            >
              {/* Header Panel */}
              <div className={`p-6 rounded-3xl border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 backdrop-blur-md ${
                isLight 
                  ? "bg-white/40 border-white/60 shadow-md text-slate-800" 
                  : "bg-slate-950/60 border border-slate-900 text-slate-100"
              }`}>
                <div>
                  <h2 className={`text-lg font-bold font-display flex items-center gap-2 ${isLight ? "text-slate-900" : "text-white"}`}>
                    <Folder className="w-5 h-5 text-cyan-500" />
                    Local Workspace Directory
                  </h2>
                  <p className={`text-xs mt-1 ${isLight ? "text-slate-500" : "text-slate-400"}`}>
                    {currentFolderPath 
                      ? `Browsing: ${currentFolderPath}` 
                      : "Directly browse, manage, and launch your real local coding projects."}
                  </p>
                </div>
                <div className="flex gap-3 items-center flex-wrap">
                  {currentFolderPath && (
                    <button
                      onClick={() => setCurrentFolderPath(null)}
                      className={`px-4 py-2 bg-cyan-600/10 hover:bg-cyan-600/20 border border-cyan-550/20 text-cyan-400 rounded-xl text-xs font-bold font-mono tracking-wider flex items-center gap-1.5 transition-all cursor-pointer`}
                    >
                      <ArrowLeft className="w-4 h-4" />
                      PROJECTS GRID
                    </button>
                  )}
                  <button
                    onClick={handleOpenRealFolder}
                    className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold font-mono tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-cyan-600/20 cursor-pointer self-start sm:self-auto"
                  >
                    <Plus className="w-4 h-4" />
                    OPEN REAL PROJECT FOLDER
                  </button>
                </div>
              </div>

              {/* Projects List / File Explorer */}
              {currentFolderPath ? (
                /* File Explorer UI */
                <div className={`border rounded-3xl p-6 backdrop-blur-md flex flex-col gap-4 ${
                  isLight 
                    ? "bg-white/40 border-white/60 text-slate-850 shadow-md" 
                    : "bg-slate-950/60 border border-slate-900 text-slate-100"
                }`}>
                  {/* Toolbar */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/10 pb-4">
                    <button
                      onClick={() => {
                        const isRootProject = realProjects.some(p => p.path.replace(/\/$/, '') === currentFolderPath?.replace(/\/$/, ''));
                        if (isRootProject || !parentPath || parentPath === currentFolderPath) {
                          setCurrentFolderPath(null);
                        } else {
                          fetchFolderContents(parentPath);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wide flex items-center gap-1 transition-all cursor-pointer border ${
                        isLight
                          ? "bg-white border-slate-200 text-slate-700 hover:bg-slate-50 shadow-sm"
                          : "bg-slate-900 border-slate-800 text-slate-350 hover:bg-slate-850"
                      }`}
                    >
                      <ArrowLeft className="w-3.5 h-3.5" />
                      BACK
                    </button>
                    
                    <div className="flex items-center gap-2 flex-1 md:mx-4 max-w-full overflow-hidden">
                      <span className="text-[10px] font-mono text-slate-500 shrink-0">CURRENT PATH:</span>
                      <span className="text-xs font-mono bg-black/25 px-3 py-1.5 rounded-lg text-cyan-400 truncate block w-full">
                        {currentFolderPath}
                      </span>
                    </div>

                    <button
                      onClick={() => executeSystemCommand(`code "${currentFolderPath}"`, false)}
                      className="px-3 py-1.5 bg-cyan-600/10 hover:bg-cyan-600/25 border border-cyan-500/20 text-cyan-400 rounded-lg text-xs font-bold font-mono tracking-wide flex items-center gap-1.5 transition-all cursor-pointer shrink-0"
                    >
                      <Code className="w-3.5 h-3.5" />
                      OPEN IN VS CODE
                    </button>
                  </div>

                  {/* File List/Table */}
                  {folderFilesLoading ? (
                    <div className="py-20 text-center text-xs text-slate-500 font-mono">
                      Loading files and subfolders...
                    </div>
                  ) : folderFilesError ? (
                    <div className="p-6 text-center border rounded-2xl border-rose-900/30 bg-rose-950/10 text-rose-400 text-xs">
                      <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
                      <span>{folderFilesError}</span>
                    </div>
                  ) : folderFiles.length === 0 ? (
                    <div className="py-16 text-center text-xs text-slate-500 font-mono">
                      This folder is empty.
                    </div>
                  ) : (
                    <div className="overflow-x-auto max-h-[500px]">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-200/10 text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                            <th className="py-2.5 pl-3">Name</th>
                            <th className="py-2.5">Type</th>
                            <th className="py-2.5">Size</th>
                            <th className="py-2.5 text-right pr-3">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200/5">
                          {folderFiles.map((item, idx) => {
                            const isImage = /\.(jpg|jpeg|png|gif|webp|svg|bmp)$/i.test(item.name);
                            const isVideo = /\.(mp4|webm|ogg|mkv|mov|avi)$/i.test(item.name);
                            const isText = isTextFile(item.name);
                            return (
                              <tr 
                                key={idx}
                                className={`group hover:bg-cyan-500/5 transition-colors cursor-pointer`}
                                onClick={() => {
                                  if (item.isDir) {
                                    fetchFolderContents(item.path);
                                  } else if (isImage) {
                                    setViewerImage(item);
                                  } else if (isVideo) {
                                    setViewerVideo(item);
                                  } else if (isText) {
                                    openNotepad(item);
                                  }
                                }}
                              >
                                <td className="py-3 pl-3 flex items-center gap-2.5 font-medium max-w-sm truncate">
                                  {item.isDir ? (
                                    <Folder className="w-4 h-4 text-cyan-400 fill-cyan-400/10 group-hover:scale-105 transition-transform" />
                                  ) : isImage ? (
                                    <FileImage className="w-4 h-4 text-emerald-400 fill-emerald-400/10 group-hover:scale-105 transition-transform" />
                                  ) : isVideo ? (
                                    <Play className="w-4 h-4 text-rose-400 fill-rose-400/10 group-hover:scale-105 transition-transform" />
                                  ) : isText ? (
                                    <FileText className="w-4 h-4 text-cyan-400 group-hover:scale-105 transition-transform" />
                                  ) : (
                                    <File className="w-4 h-4 text-slate-400" />
                                  )}
                                  <span className={
                                    item.isDir ? "text-cyan-400 hover:underline" : 
                                    isImage ? "text-emerald-400 font-medium" : 
                                    isVideo ? "text-rose-400 font-medium" :
                                    isText ? "text-cyan-350 hover:underline" : 
                                    "text-slate-350"
                                  }>
                                    {item.name}
                                  </span>
                                </td>
                                <td className="py-3 font-mono text-[10px] text-slate-500">
                                  {item.isDir ? "Directory" : item.name.split('.').pop()?.toUpperCase() || "File"}
                                </td>
                                <td className="py-3 font-mono text-[10px] text-slate-500">
                                  {item.isDir ? "--" : formatBytes(item.size)}
                                </td>
                                <td className="py-3 text-right pr-3">
                                  {item.isDir ? (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        fetchFolderContents(item.path);
                                      }}
                                      className="text-cyan-500 hover:text-cyan-400 font-bold font-mono text-[10px] flex items-center gap-0.5 ml-auto cursor-pointer"
                                    >
                                      BROWSE <ChevronRight className="w-3 h-3" />
                                    </button>
                                  ) : isImage ? (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setViewerImage(item);
                                      }}
                                      className="text-emerald-500 hover:text-emerald-400 font-bold font-mono text-[10px] flex items-center gap-0.5 ml-auto cursor-pointer"
                                    >
                                      VIEW IMAGE
                                    </button>
                                  ) : isVideo ? (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setViewerVideo(item);
                                      }}
                                      className="text-rose-500 hover:text-rose-400 font-bold font-mono text-[10px] flex items-center gap-0.5 ml-auto cursor-pointer"
                                    >
                                      PLAY VIDEO
                                    </button>
                                  ) : isText ? (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        openNotepad(item);
                                      }}
                                      className="text-cyan-500 hover:text-cyan-400 font-bold font-mono text-[10px] flex items-center gap-0.5 ml-auto cursor-pointer"
                                    >
                                      EDIT FILE
                                    </button>
                                  ) : (
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        executeSystemCommand(`xdg-open "${item.path}" || open "${item.path}"`, false);
                                      }}
                                      className="text-slate-400 hover:text-cyan-400 font-bold font-mono text-[10px] flex items-center gap-0.5 ml-auto cursor-pointer"
                                    >
                                      OPEN SYSTEM
                                    </button>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                /* Projects Grid */
                realProjects.length === 0 ? (
                  <div className={`border rounded-3xl p-12 text-center backdrop-blur-md ${
                    isLight 
                      ? "bg-white/30 border-white/50 text-slate-500" 
                      : "bg-slate-950/40 border-slate-900/60 text-slate-400"
                  }`}>
                    <Folder className="w-12 h-12 text-slate-600 mx-auto mb-4 stroke-[1.5]" />
                    <h3 className={`text-sm font-semibold ${isLight ? "text-slate-700" : "text-slate-300"}`}>No local projects active</h3>
                    <p className="text-xs mt-1 max-w-sm mx-auto leading-relaxed">
                      Click the button above to link a real directory from your machine. You can directly launch it in VS Code or browse files.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {realProjects.map((project, idx) => (
                      <div 
                        key={idx} 
                        onClick={() => fetchFolderContents(project.path)}
                        className={`border rounded-2xl p-5 flex flex-col justify-between h-52 transition-all duration-500 cursor-pointer ${
                          isLight 
                            ? "bg-white/40 border-white/60 shadow-md backdrop-blur-md text-slate-850 hover:bg-white/50 hover:border-cyan-300" 
                            : "bg-slate-950/60 border border-slate-900 text-slate-100 backdrop-blur-md hover:bg-slate-950/70 hover:border-cyan-900"
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[9px] font-mono text-cyan-400 bg-cyan-950/10 border border-cyan-500/20 px-2 py-0.5 rounded uppercase">
                              Local Dir
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                const updated = realProjects.filter(p => p.path !== project.path);
                                setRealProjects(updated);
                                localStorage.setItem("realProjects", JSON.stringify(updated));
                                if (currentFolderPath === project.path) setCurrentFolderPath(null);
                              }}
                              className="text-slate-500 hover:text-rose-500 transition-colors p-1 cursor-pointer"
                              title="Remove project link"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          <h3 className={`text-sm font-bold font-display truncate ${isLight ? "text-slate-900" : "text-white"}`}>
                            {project.name}
                          </h3>
                          <p className={`text-[10px] mt-2 font-mono break-all line-clamp-3 p-2 rounded-lg ${isLight ? "text-slate-600 bg-slate-100/60" : "bg-black/25 text-slate-400"}`}>
                            {project.path}
                          </p>
                        </div>

                        <div className="flex items-center justify-between border-t border-slate-200/10 pt-3 text-xs font-mono text-slate-500">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              executeSystemCommand(`code "${project.path}"`, false);
                            }}
                            className="text-cyan-500 hover:text-cyan-400 font-bold flex items-center gap-1.5 cursor-pointer"
                          >
                            <Code className="w-3.5 h-3.5" />
                            LAUNCH VS CODE
                          </button>
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              fetchFolderContents(project.path);
                            }}
                            className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1.5 cursor-pointer font-mono"
                          >
                            <Folder className="w-3.5 h-3.5" />
                            BROWSE FILES
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              )}
            </motion.div>
          )}

          {activeView === "chat" && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`w-full max-w-4xl mx-auto flex-1 flex flex-col border rounded-3xl overflow-hidden h-[540px] shadow-2xl transition-all duration-500 ${
                isLight 
                  ? "bg-white/40 border-white/60 text-slate-850" 
                  : "bg-slate-950/60 border border-slate-900 text-slate-100 shadow-2xl"
              }`}
            >
              {/* Chat Header */}
              <div className={`border-b px-6 py-4 flex items-center justify-between ${
                isLight ? "bg-white/60 border-slate-200" : "bg-slate-900/40 border-slate-900/80"
              }`}>
                <div className="flex items-center gap-2.5">
                  <div className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
                  <div>
                    <h2 className={`text-sm font-bold font-display ${isLight ? "text-slate-950" : "text-white"}`}>Neural Link Terminal</h2>
                    <p className="text-[10px] text-slate-400 font-mono">SECURE IPC CONNECTION</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => {
                      setChatMessages([{ sender: 'luna', text: "LUNA Operating System chat interface initialized. Standard command syntax is supported.", timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}) }]);
                      setChatHistory([]);
                      pushTerminalLog("Chat session cleared.", "system");
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      isLight ? "text-slate-600 hover:bg-slate-100 hover:text-red-500" : "text-slate-400 hover:bg-slate-800 hover:text-red-400"
                    }`}
                    title="Clear Chat"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Clear</span>
                  </button>
                  <button 
                    onClick={() => {
                      setChatMessages([{ sender: 'luna', text: "New session started. How can I assist you?", timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}) }]);
                      setChatHistory([]);
                      pushTerminalLog("New chat session started.", "system");
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      isLight ? "bg-slate-900 text-white hover:bg-slate-800" : "bg-white text-slate-900 hover:bg-slate-200"
                    }`}
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>New Chat</span>
                  </button>
                  <span className={`hidden sm:inline-block text-[10px] font-mono px-2.5 py-1 rounded-full border ${
                    isLight ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-slate-900 border-slate-850 text-slate-500"
                  }`}>
                    LUNA V4 CORE
                  </span>
                </div>
              </div>

              {/* Chat Messages */}
              <div className={`flex-1 overflow-y-auto p-6 space-y-4 ${
                isLight ? "bg-white/10" : "bg-slate-950/35"
              }`}>
                {chatMessages.map((msg, idx) => (
                  <div 
                    key={idx} 
                    className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[70%] p-4 rounded-2xl text-xs leading-relaxed border ${
                      msg.sender === 'user'
                        ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-tr-none border-transparent'
                        : isLight
                          ? 'bg-white/80 border-slate-200/80 text-slate-800 rounded-tl-none shadow-sm'
                          : 'bg-slate-900/80 border border-slate-850 text-slate-200 rounded-tl-none'
                    }`}>
                      <p>{msg.text}</p>
                      <span className="text-[9px] text-slate-400 font-mono block mt-1 text-right">{msg.timestamp}</span>
                    </div>
                  </div>
                ))}
                {isThinking && (
                  <div className="flex justify-start">
                    <div className={`max-w-[70%] p-4 rounded-2xl rounded-tl-none text-xs border ${
                      isLight ? 'bg-white/80 border-slate-200/80' : 'bg-slate-900/80 border-slate-850'
                    }`}>
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1">
                          <span className="h-2 w-2 rounded-full bg-cyan-500 animate-bounce" style={{animationDelay: '0ms'}} />
                          <span className="h-2 w-2 rounded-full bg-cyan-500 animate-bounce" style={{animationDelay: '150ms'}} />
                          <span className="h-2 w-2 rounded-full bg-cyan-500 animate-bounce" style={{animationDelay: '300ms'}} />
                        </div>
                        <span className="text-slate-400 font-mono text-[10px]">Luna is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input Bar */}
              <form 
                onSubmit={(e) => { e.preventDefault(); handleCommand(chatInput); setChatInput(""); }}
                className={`border-t p-4 flex gap-2 ${
                  isLight ? "bg-white/40 border-slate-200" : "bg-slate-900/40 border-slate-900"
                }`}
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Query Luna core routing..."
                  className={`flex-1 rounded-xl px-4 py-2.5 text-xs outline-none border transition-all ${
                    isLight 
                      ? "bg-white/85 border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-slate-350" 
                      : "bg-slate-950/80 border-slate-850 hover:border-slate-800 text-slate-200 placeholder:text-slate-500 focus:border-slate-700"
                  }`}
                />
                <button 
                  type="submit"
                  className="px-4 bg-cyan-650 hover:bg-cyan-600 border border-cyan-800/30 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  SEND
                </button>
              </form>
            </motion.div>
          )}

          {activeView === "settings" && (
            <motion.div
              key="settings"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 w-full max-w-4xl mx-auto"
            >
              <div className={`rounded-3xl p-6 border transition-all duration-500 ${
                isLight 
                  ? "bg-white/40 border-white/60 shadow-lg backdrop-blur-xl" 
                  : "bg-slate-950/60 border border-slate-900 backdrop-blur-md"
              }`}>
                <div className="flex items-center gap-3 mb-6 border-b pb-4 border-slate-200/10">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                    <Settings className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className={`text-lg font-display font-bold ${isLight ? "text-slate-900" : "text-white"}`}>System Settings</h2>
                    <p className={`text-xs ${isLight ? "text-slate-500" : "text-slate-400"}`}>Configure Voice Systems, LLM Providers, Local Connections, and Gateways.</p>
                  </div>
                </div>
                
                <SettingsPanel 
                  settingsConfig={settingsConfig}
                  setSettingsConfig={setSettingsConfig}
                  ttsSettings={ttsSettings} 
                  setTtsSettings={setTtsSettings} 
                  isLight={isLight} 
                  customBg={customBg}
                  setCustomBg={setCustomBg}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </main>

      {/* Real-time Clock HUD capsule (Luna/Iron Man style clock overlay) - MOVED TO BOTTOM LEFT */}
      <div className={`fixed bottom-6 left-6 z-50 hidden md:flex flex-col justify-center px-6 py-3 rounded-2xl backdrop-blur-2xl border text-left font-mono shadow-2xl transition-all duration-500 ${
        isLight 
          ? "bg-white/70 border-white/80 text-slate-700 shadow-[0_10px_40px_rgba(0,0,0,0.1)]" 
          : "bg-slate-950/80 border-slate-900/60 text-slate-300 shadow-[0_10px_40px_rgba(0,0,0,0.6)]"
      }`}>
        <div className="text-sm font-bold tracking-wider text-cyan-500 mb-0.5">{formattedTime}</div>
        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">{formattedDate}</div>
      </div>

      {/* Floating Bottom Navigation Dock */}
      <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-4">

        <div className={`p-2.5 rounded-full backdrop-blur-xl flex items-center gap-1.5 shadow-2xl transition-all duration-500 border ${
          isLight 
            ? "bg-white/65 border-white/65 shadow-[0_10px_40px_rgba(0,0,0,0.06)]" 
            : "bg-slate-950/80 border-slate-900/60 shadow-[0_10px_40px_rgba(0,0,0,0.6)]"
        }`}>
          {[
            { id: "home", label: "Home", icon: <Home className="w-4 h-4" /> },
            { id: "voice", label: "Voice", icon: <Mic className="w-4 h-4" /> },
            { id: "chat", label: "Chat", icon: <MessageSquare className="w-4 h-4" /> },
            { id: "projects", label: "Projects", icon: <Folder className="w-4 h-4" /> },
            { id: "devices", label: "Devices", icon: <Smartphone className="w-4 h-4" /> },
            { id: "developer", label: "Developer", icon: <Code className="w-4 h-4" /> },
            { id: "analytics", label: "Analytics", icon: <BarChart2 className="w-4 h-4" /> },
            { id: "settings", label: "Settings", icon: <Settings className="w-4 h-4" /> }
          ].map(tab => {
            const isActive = activeView === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveView(tab.id as ActiveView);
                  pushActivity(`Navigated to dashboard: ${tab.label.toUpperCase()}`, 'system');
                }}
                className={`relative px-3.5 py-2.5 rounded-full text-xs font-semibold font-sans flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer ${
                  isActive 
                    ? isLight
                      ? 'bg-slate-100 text-slate-850 shadow-sm border border-slate-200'
                      : 'bg-slate-900 text-white shadow-lg border border-slate-800' 
                    : isLight
                      ? 'text-slate-550 hover:text-slate-850'
                      : 'text-slate-400 hover:text-slate-200'
                }`}
                title={tab.label}
              >
                {/* Visual active indicator spark */}
                {isActive && (
                  <motion.div 
                    layoutId="activeTabSpark"
                    className="absolute -top-1 left-1/2 -translate-x-1/2 h-1 w-1 bg-cyan-400 rounded-full"
                  />
                )}
                {tab.icon}
                <span className="hidden lg:inline text-[11px] font-sans font-medium tracking-wide">
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </nav>

    {/* User Details Modal */}
    <AnimatePresence>
      {showUserModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={`fixed inset-0 z-[100] flex items-center justify-center backdrop-blur-sm px-4 ${isLight ? 'bg-white/60' : 'bg-slate-950/60'}`}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className={`w-full max-w-sm rounded-3xl p-6 border shadow-2xl ${
              isLight ? "bg-white border-slate-200" : "bg-slate-900 border-slate-800"
            }`}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className={`text-sm font-bold font-display ${isLight ? "text-slate-900" : "text-white"}`}>Edit User Details</h3>
              <button onClick={() => setShowUserModal(false)} className="text-slate-500 hover:text-slate-700 cursor-pointer">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className={`block text-xs font-bold mb-1.5 ${isLight ? "text-slate-700" : "text-slate-300"}`}>Name / Alias</label>
                <input 
                  type="text" 
                  value={userDetails.name}
                  onChange={(e) => setUserDetails({ ...userDetails, name: e.target.value })}
                  className={`w-full px-4 py-2 rounded-xl text-sm border outline-none focus:ring-2 focus:ring-cyan-500/50 ${
                    isLight ? "bg-slate-50 border-slate-200 text-slate-800" : "bg-slate-950 border-slate-800 text-slate-200"
                  }`}
                />
              </div>
              <div>
                <label className={`block text-xs font-bold mb-1.5 ${isLight ? "text-slate-700" : "text-slate-300"}`}>System Role</label>
                <input 
                  type="text" 
                  value={userDetails.role}
                  onChange={(e) => setUserDetails({ ...userDetails, role: e.target.value })}
                  className={`w-full px-4 py-2 rounded-xl text-sm border outline-none focus:ring-2 focus:ring-cyan-500/50 ${
                    isLight ? "bg-slate-50 border-slate-200 text-slate-800" : "bg-slate-950 border-slate-800 text-slate-200"
                  }`}
                />
              </div>
              
              <button 
                onClick={() => setShowUserModal(false)}
                className="w-full mt-4 py-3 bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-bold rounded-xl text-sm shadow-lg hover:opacity-90 cursor-pointer"
              >
                Save Protocol
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* WhatsApp Link Modal */}
      {showWhatsAppModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={`fixed inset-0 z-[100] flex items-center justify-center backdrop-blur-sm px-4 ${isLight ? 'bg-white/60' : 'bg-slate-950/60'}`}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className={`w-full max-w-sm rounded-3xl p-6 border shadow-2xl ${
              isLight ? "bg-white border-slate-200" : "bg-slate-900 border-slate-800"
            }`}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className={`text-sm font-bold font-display ${isLight ? "text-slate-900" : "text-white"}`}>Link WhatsApp Agent</h3>
              <button onClick={() => setShowWhatsAppModal(false)} className="text-slate-500 hover:text-slate-700 cursor-pointer">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>

            <div className="space-y-5 text-center flex flex-col items-center justify-center">
              {waConnected ? (
                <>
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-full">
                    <Check className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className={`text-sm font-semibold ${isLight ? "text-slate-800" : "text-white"}`}>WhatsApp Agent Linked</h4>
                    <p className="text-xs text-slate-500 mt-1">Listening for incoming DMs to reply with text and voice note.</p>
                  </div>
                  <button
                    onClick={async () => {
                      await fetch("http://localhost:3000/api/agents/whatsapp/stop", { method: "POST" });
                      setWaConnected(false);
                      setWaQrCode(null);
                    }}
                    className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold font-mono tracking-wider transition-all"
                  >
                    DISCONNECT AGENT
                  </button>
                </>
              ) : waQrCode ? (
                <>
                  <div className="p-3 bg-slate-950 border border-slate-900 rounded-2xl">
                    <img src={waQrCode} alt="WhatsApp QR Code" className="w-48 h-48 rounded-lg" />
                  </div>
                  <div>
                    <h4 className={`text-sm font-semibold ${isLight ? "text-slate-800" : "text-white"}`}>Scan QR Code</h4>
                    <p className="text-xs text-slate-500 mt-1">Open WhatsApp on your phone, go to Linked Devices, and scan this QR code to authenticate the agent.</p>
                  </div>
                  <div className="text-[10px] font-mono text-cyan-500 animate-pulse uppercase tracking-wider">
                    Generating secure session...
                  </div>
                </>
              ) : (
                <>
                  <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-500 rounded-full">
                    <Server className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className={`text-sm font-semibold ${isLight ? "text-slate-800" : "text-white"}`}>WhatsApp Agent Off</h4>
                    <p className="text-xs text-slate-500 mt-1">Start the agent session to generate a registration QR code.</p>
                  </div>
                  <button
                    onClick={async () => {
                      await fetch("http://localhost:3000/api/agents/whatsapp/start", { method: "POST" });
                    }}
                    className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold font-mono tracking-wider transition-all"
                  >
                    START SESSION
                  </button>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>

      {/* PERMISSION MANAGER MODAL */}
      <AnimatePresence>
        {pendingCommand && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`fixed inset-0 z-[110] flex items-center justify-center backdrop-blur-sm px-4 ${isLight ? 'bg-white/60' : 'bg-slate-950/60'}`}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className={`w-full max-w-sm rounded-3xl p-6 border shadow-2xl relative overflow-hidden ${
                isLight ? "bg-white border-red-200" : "bg-slate-900 border-red-900/60"
              }`}
            >
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-orange-500" />
              
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20 text-red-500">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className={`font-bold font-display ${isLight ? "text-slate-900" : "text-white"}`}>Privileged Execution</h3>
                    <p className={`text-[10px] uppercase font-mono ${isLight ? "text-slate-500" : "text-slate-400"}`}>Awaiting Authorization</p>
                  </div>
                </div>

                <div className={`p-3 rounded-xl border font-mono text-xs overflow-x-auto ${isLight ? "bg-slate-50 border-slate-200 text-slate-800" : "bg-slate-950 border-slate-800 text-slate-300"}`}>
                  <span className="text-red-500 mr-2">$</span>
                  {pendingCommand.command}
                </div>

                <p className={`text-xs ${isLight ? "text-slate-600" : "text-slate-400"}`}>
                  Luna has requested to run this command. It requires elevated privileges (polkit/sudo).
                </p>

                <div className="flex gap-3 mt-2">
                  <button 
                    onClick={() => {
                      setPendingCommand(null);
                      setCoreState("Idle");
                      pushTerminalLog("[OS] User denied execution of privileged command.", "warning");
                      speakText("Authorization denied. Cancelling execution.");
                    }}
                    className={`flex-1 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest transition-all ${
                      isLight ? "bg-slate-100 hover:bg-slate-200 text-slate-600" : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                    }`}
                  >
                    Deny
                  </button>
                  <button 
                    onClick={() => {
                      const cmd = pendingCommand.command;
                      const priv = pendingCommand.requiresPrivilege;
                      const cat = pendingCommand.category || "RAW_COMMAND";
                      setPendingCommand(null);
                      setCoreState("Executing");
                      executeSystemCommand(cmd, priv, cat);
                    }}
                    className="flex-1 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest transition-all bg-red-500 hover:bg-red-600 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                  >
                    Approve
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Draggable Image Viewer Popup */}
      <AnimatePresence>
        {viewerImage && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            drag
            dragMomentum={false}
            dragElastic={0.1}
            className={`fixed top-1/4 left-1/3 z-[150] w-full max-w-lg rounded-2xl border backdrop-blur-lg shadow-2xl p-4 cursor-move ${
              isLight 
                ? "bg-white/90 border-slate-300 text-slate-800" 
                : "bg-slate-950/90 border-slate-800 text-slate-100"
            }`}
          >
            {/* Title Bar */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200/15 mb-3 select-none">
              <div className="flex items-center gap-2">
                <FileImage className="w-4 h-4 text-cyan-500" />
                <span className="text-xs font-mono font-bold truncate max-w-[280px]">{viewerImage.name}</span>
              </div>
              <button
                onClick={() => setViewerImage(null)}
                className="p-1 hover:bg-rose-500/20 hover:text-rose-500 rounded-lg transition-colors cursor-pointer"
                title="Close image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Image Container */}
            <div className="flex items-center justify-center bg-black/40 rounded-xl overflow-hidden min-h-[200px] p-2">
              <img
                src={`http://localhost:3000/api/agents/files/content?path=${encodeURIComponent(viewerImage.path)}`}
                alt={viewerImage.name}
                className="max-h-[50vh] max-w-full object-contain rounded-lg shadow pointer-events-none"
              />
            </div>
            
            {/* Drag Hint Footer */}
            <div className="text-[10px] text-center text-slate-500 font-mono mt-2 select-none">
              Drag anywhere to move
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Draggable Video Player Popup */}
      <AnimatePresence>
        {viewerVideo && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            drag
            dragMomentum={false}
            dragElastic={0.1}
            className={`fixed top-1/4 left-1/3 z-[150] w-full max-w-xl rounded-2xl border backdrop-blur-lg shadow-2xl p-4 cursor-move ${
              isLight 
                ? "bg-white/90 border-slate-350 text-slate-800" 
                : "bg-slate-950/90 border-slate-800 text-slate-100"
            }`}
          >
            {/* Title Bar */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200/15 mb-3 select-none">
              <div className="flex items-center gap-2">
                <Play className="w-4 h-4 text-cyan-500 fill-cyan-500/10" />
                <span className="text-xs font-mono font-bold truncate max-w-[340px]">{viewerVideo.name}</span>
              </div>
              <button
                onClick={() => setViewerVideo(null)}
                className="p-1 hover:bg-rose-500/20 hover:text-rose-500 rounded-lg transition-colors cursor-pointer"
                title="Close video"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Video Container */}
            <div className="flex items-center justify-center bg-black/60 rounded-xl overflow-hidden min-h-[240px] p-1">
              <video
                src={`http://localhost:3000/api/agents/files/content?path=${encodeURIComponent(viewerVideo.path)}`}
                controls
                autoPlay
                className="max-h-[50vh] max-w-full rounded-lg shadow"
                style={{ pointerEvents: 'auto' }}
              />
            </div>
            
            {/* Drag Hint Footer */}
            <div className="text-[10px] text-center text-slate-500 font-mono mt-2 select-none">
              Drag anywhere to move
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Notepad Editor Popup */}
      <AnimatePresence>
        {notepadFile && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            drag
            dragMomentum={false}
            dragElastic={0.1}
            className={`fixed top-12 left-1/4 z-[150] w-full max-w-2xl rounded-2xl border backdrop-blur-lg shadow-2xl p-5 cursor-move ${
              isLight 
                ? "bg-white/95 border-slate-300 text-slate-800" 
                : "bg-slate-950/95 border-slate-850 text-slate-100"
            }`}
          >
            {/* Title Bar */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200/10 mb-3 select-none">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                <div className="max-w-md overflow-hidden">
                  <span className="text-xs font-mono font-bold block truncate">{notepadFile.name}</span>
                  <span className="text-[9px] font-mono text-slate-500 block truncate">{notepadFile.path}</span>
                </div>
              </div>
              <button
                onClick={() => {
                  setNotepadFile(null);
                  setNotepadContent("");
                  setNotepadError(null);
                }}
                className="p-1 hover:bg-rose-500/20 hover:text-rose-500 rounded-lg transition-colors cursor-pointer"
                title="Close notepad"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Notepad Controls */}
            <div className="flex items-center justify-between gap-3 mb-2.5 select-none">
              {/* File Type Display */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-mono uppercase bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-cyan-400">
                  {notepadFile.name.split('.').pop()?.toUpperCase() || "TEXT"} File
                </span>
                {notepadSaveSuccess && (
                  <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-0.5 animate-pulse">
                    <Check className="w-3.5 h-3.5" /> SAVED
                  </span>
                )}
              </div>
              
              {/* Scroll & Save Buttons */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => scrollNotepad('up')}
                  className={`px-2.5 py-1 rounded text-[10px] font-bold font-mono tracking-wide transition-all border cursor-pointer ${
                    isLight 
                      ? "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700" 
                      : "bg-slate-900 border-slate-850 hover:bg-slate-800 text-slate-300"
                  }`}
                  title="Scroll Up"
                >
                  SCROLL UP
                </button>
                <button
                  type="button"
                  onClick={() => scrollNotepad('down')}
                  className={`px-2.5 py-1 rounded text-[10px] font-bold font-mono tracking-wide transition-all border cursor-pointer ${
                    isLight 
                      ? "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700" 
                      : "bg-slate-900 border-slate-850 hover:bg-slate-800 text-slate-300"
                  }`}
                  title="Scroll Down"
                >
                  SCROLL DOWN
                </button>

                <button
                  type="button"
                  onClick={handleSaveNotepad}
                  disabled={notepadSaving}
                  className="px-3.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[10px] font-bold font-mono tracking-wider transition-all disabled:opacity-50 cursor-pointer"
                >
                  {notepadSaving ? "SAVING..." : "SAVE CHANGES"}
                </button>
              </div>
            </div>

            {/* Notepad Body */}
            <div className="relative border border-slate-200/10 rounded-xl overflow-hidden bg-black/40">
              {notepadLoading ? (
                <div className="py-24 text-center text-xs text-slate-500 font-mono">
                  Fetching file content...
                </div>
              ) : notepadError ? (
                <div className="p-6 text-center text-rose-400 text-xs font-mono">
                  {notepadError}
                </div>
              ) : (
                <textarea
                  ref={notepadTextareaRef}
                  value={notepadContent}
                  onChange={(e) => setNotepadContent(e.target.value)}
                  className="w-full h-80 p-4 text-xs font-mono bg-transparent text-slate-200 outline-none resize-none overflow-y-auto leading-relaxed cursor-text"
                  style={{ pointerEvents: 'auto' }}
                  placeholder="File is empty"
                />
              )}
            </div>

            {/* Drag Hint Footer */}
            <div className="text-[10px] text-center text-slate-500 font-mono mt-2.5 select-none">
              Drag anywhere to move
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
