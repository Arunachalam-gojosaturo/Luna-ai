import React, { useState } from "react";
import { motion } from "motion/react";
import { Smartphone, Monitor, Laptop, RefreshCw, Cpu, HardDrive, Battery, Wifi, Activity, Terminal, ShieldAlert, Sparkles, Play, Power, ArrowLeft, Home, Volume2, VolumeX, AlertCircle } from "lucide-react";
import { DeviceTelemetry } from "../types";

interface DeviceEcosystemProps {
  devices: DeviceTelemetry[];
  onSyncDevice: (id: string) => void;
  onToggleTask: (deviceId: string, task: string) => void;
  onOpenMobileScreen?: () => void;
  isLight?: boolean;
}

export default function DeviceEcosystem({
  devices,
  onSyncDevice,
  onToggleTask,
  onOpenMobileScreen,
  isLight = false
}: DeviceEcosystemProps) {
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>(devices[1]?.id || devices[0]?.id || "");

  const [adbIp, setAdbIp] = useState(() => localStorage.getItem("adbIp") || "192.168.1.100");
  const [adbPort, setAdbPort] = useState(() => localStorage.getItem("adbPort") || "5555");
  const [adbStatus, setAdbStatus] = useState<string>("");
  const [isConnecting, setIsConnecting] = useState<boolean>(false);

  interface RealADBDevice {
    serial: string;
    status: string;
    model: string;
    is_wireless: boolean;
  }

  const [realDevices, setRealDevices] = useState<RealADBDevice[]>([]);
  const [realDevicesLoading, setRealDevicesLoading] = useState<boolean>(false);
  const [selectedRealDevice, setSelectedRealDevice] = useState<string>("");

  const fetchRealADBDevices = async () => {
    try {
      const response = await fetch("http://localhost:3000/api/agents/adb/devices");
      const data = await response.json();
      if (data.status === "success") {
        setRealDevices(data.devices);
        if (data.devices.length > 0 && !selectedRealDevice) {
          setSelectedRealDevice(data.devices[0].serial);
        }
      }
    } catch (e) {
      console.error("Error fetching ADB devices:", e);
    }
  };

  React.useEffect(() => {
    fetchRealADBDevices();
    const interval = setInterval(fetchRealADBDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAdbConnect = async () => {
    setIsConnecting(true);
    setAdbStatus("Connecting...");
    localStorage.setItem("adbIp", adbIp);
    localStorage.setItem("adbPort", adbPort);
    try {
      const response = await fetch("http://localhost:3000/api/agents/adb/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: `${adbIp}:${adbPort}` })
      });
      const data = await response.json();
      if (data.status === "success") {
        setAdbStatus(`Connected to ${adbIp}:${adbPort}`);
        fetchRealADBDevices();
      } else {
        setAdbStatus(`Failed: ${data.stderr || data.stdout || "Unknown error"}`);
      }
    } catch (e: any) {
      setAdbStatus(`Error: ${e.message}`);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleAdbTcpIp = async (serial: string) => {
    setAdbStatus(`Enabling Wireless (TCP/IP 5555) on ${serial}...`);
    try {
      const response = await fetch("http://localhost:3000/api/agents/adb/tcpip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ serial, port: adbPort })
      });
      const data = await response.json();
      if (data.status === "success") {
        setAdbStatus(`Wireless TCP/IP mode enabled on ${serial}. You can now connect to its IP address wirelessly.`);
        fetchRealADBDevices();
      } else {
        setAdbStatus(`Wireless setup failed: ${data.stderr || data.stdout || "Make sure device is connected & authorized"}`);
      }
    } catch (e: any) {
      setAdbStatus(`Wireless error: ${e.message}`);
    }
  };

  const handleAdbDisconnect = async (target: string) => {
    setAdbStatus(`Disconnecting wireless device ${target}...`);
    try {
      const response = await fetch("http://localhost:3000/api/agents/adb/disconnect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target })
      });
      const data = await response.json();
      if (data.status === "success") {
        setAdbStatus(`Successfully disconnected ${target}`);
        if (selectedRealDevice === target) {
          setSelectedRealDevice("");
        }
        fetchRealADBDevices();
      } else {
        setAdbStatus(`Disconnect failed: ${data.stderr || data.stdout}`);
      }
    } catch (e: any) {
      setAdbStatus(`Disconnect error: ${e.message}`);
    }
  };

  const handleAdbScrcpy = async () => {
    try {
      const target = selectedRealDevice || `${adbIp}:${adbPort}`;
      const response = await fetch("http://localhost:3000/api/agents/adb/scrcpy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target })
      });
      const data = await response.json();
      if (data.status === "success") {
        setAdbStatus(`Launched scrcpy mirror for ${target}`);
      } else {
        setAdbStatus(`Mirror failed: ${data.result}`);
      }
    } catch (e: any) {
      setAdbStatus(`Error launching mirror: ${e.message}`);
    }
  };

  const handleAdbControl = async (action: string) => {
    try {
      const target = selectedRealDevice || `${adbIp}:${adbPort}`;
      const response = await fetch("http://localhost:3000/api/agents/adb/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, target })
      });
      const data = await response.json();
      if (data.status !== "success") {
        setAdbStatus(`Control failed: ${data.result || data.stderr}`);
      }
    } catch (e: any) {
      console.error("Control error:", e);
    }
  };

  const activeDevice = devices.find(d => d.id === selectedDeviceId) || devices[0];

  const getDeviceIcon = (type: 'mobile' | 'workstation' | 'desktop') => {
    switch (type) {
      case 'mobile':
        return <Smartphone className="w-5 h-5" />;
      case 'workstation':
        return <Laptop className="w-5 h-5" />;
      case 'desktop':
        return <Monitor className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: 'synced' | 'syncing' | 'offline') => {
    switch (status) {
      case 'synced':
        return 'bg-emerald-500 text-emerald-400 border-emerald-500/20';
      case 'syncing':
        return 'bg-amber-500 text-amber-400 border-amber-500/20 animate-pulse';
      case 'offline':
        return isLight ? 'bg-slate-200 text-slate-500 border-slate-300' : 'bg-slate-600 text-slate-400 border-slate-700/20';
    }
  };

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 h-full ${isLight ? 'text-slate-800' : 'text-slate-100'}`} id="device-ecosystem-container">
      {/* Device List (Left column) */}
      <div className="lg:col-span-1 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className={`text-md font-semibold tracking-tight font-display flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
            <Smartphone className="w-4 h-4 text-cyan-500" />
            Device Telemetry
          </h2>
          <span className={`text-[10px] font-mono px-2 py-0.5 border rounded-full ${isLight ? 'bg-slate-100 border-slate-300 text-slate-500' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
            {devices.length} ACTIVE NODES
          </span>
        </div>

        <div className="space-y-3 flex-1 overflow-y-auto pr-1">
          {devices.map(device => {
            const isSelected = device.id === selectedDeviceId;
            return (
              <motion.div
                key={device.id}
                onClick={() => setSelectedDeviceId(device.id)}
                className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer relative group flex flex-col gap-3 ${
                  isSelected 
                    ? (isLight ? 'bg-white/70 border-cyan-200 shadow-[0_4px_20px_rgba(6,182,212,0.15)]' : 'bg-slate-900/60 border-slate-800 shadow-[0_4px_20px_rgba(6,182,212,0.08)]')
                    : (isLight ? 'bg-white/30 border-slate-200 hover:bg-white/50 hover:border-slate-300' : 'bg-slate-950/40 border-slate-900/60 hover:bg-slate-900/30 hover:border-slate-800/50')
                }`}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                {/* Accent border glow */}
                {isSelected && (
                  <div className="absolute inset-y-4 left-0 w-1 bg-cyan-400 rounded-r-md" />
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      isSelected 
                        ? (isLight ? 'bg-cyan-50 text-cyan-600 border border-cyan-200' : 'bg-cyan-950/50 text-cyan-400 border border-cyan-800/30')
                        : (isLight ? 'bg-slate-100 text-slate-500 border border-slate-200' : 'bg-slate-900 text-slate-400 border border-slate-800')
                    }`}>
                      {getDeviceIcon(device.type)}
                    </div>
                    <div>
                      <h3 className={`text-sm font-medium ${isLight ? 'text-slate-800' : 'text-white'}`}>{device.name}</h3>
                      <p className={`text-[10px] font-mono mt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>{device.osVersion}</p>
                    </div>
                  </div>

                  <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${getStatusColor(device.syncStatus)}`}>
                    {device.syncStatus.toUpperCase()}
                  </span>
                </div>

                {/* Micro Metrics Sparkline gauges */}
                <div className={`grid grid-cols-3 gap-2 border-t pt-2.5 ${isLight ? 'border-slate-200' : 'border-slate-900/40'}`}>
                  <div className="flex flex-col">
                    <span className={`text-[9px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>CPU</span>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Cpu className="w-3 h-3 text-cyan-500" />
                      <span className={`text-xs font-mono font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{device.cpu}%</span>
                    </div>
                  </div>
                  
                  <div className="flex flex-col">
                    <span className={`text-[9px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>BATTERY</span>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Battery className={`w-3 h-3 ${device.battery < 20 ? 'text-red-500' : 'text-emerald-500'}`} />
                      <span className={`text-xs font-mono font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{device.battery}%</span>
                    </div>
                  </div>

                  <div className="flex flex-col">
                    <span className={`text-[9px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>NETWORK</span>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Wifi className="w-3 h-3 text-indigo-500" />
                      <span className={`text-[10px] font-sans font-medium truncate max-w-[48px] ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{device.network}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Selected Device Telemetry Detail (Middle & Right columns) */}
      <div className={`lg:col-span-2 flex flex-col border rounded-2xl p-6 backdrop-blur-md relative overflow-hidden ${
        isLight ? 'bg-white/60 border-slate-200/60 shadow-lg' : 'bg-slate-950/60 border-slate-900'
      }`}>
        
        {/* Soft dynamic ambient lighting backdrops */}
        <div className={`absolute right-0 top-0 w-64 h-64 blur-3xl pointer-events-none ${isLight ? 'bg-cyan-400/10' : 'bg-cyan-500/5'}`} />
        <div className={`absolute left-0 bottom-0 w-64 h-64 blur-3xl pointer-events-none ${isLight ? 'bg-indigo-400/10' : 'bg-indigo-500/5'}`} />

        {activeDevice ? (
          <div className="space-y-6 z-10 flex-1 flex flex-col justify-between">
            {/* Header section */}
            <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4 ${isLight ? 'border-slate-200' : 'border-slate-900/80'}`}>
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-xl border ${isLight ? 'bg-cyan-50 text-cyan-600 border-cyan-200' : 'bg-cyan-950/40 border-cyan-800/30 text-cyan-400'}`}>
                  {getDeviceIcon(activeDevice.type)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className={`text-lg font-semibold font-display ${isLight ? 'text-slate-900' : 'text-white'}`}>{activeDevice.name}</h2>
                    <span className={`text-[9px] font-mono border px-2 py-0.5 rounded-full ${isLight ? 'bg-cyan-100 border-cyan-200 text-cyan-700' : 'bg-cyan-950/50 border-cyan-900/50 text-cyan-400'}`}>
                      TRUSTED NODE
                    </span>
                  </div>
                  <p className={`text-xs font-mono mt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                    ID: {activeDevice.id} // OS: {activeDevice.osVersion}
                  </p>
                </div>
              </div>

              <button
                onClick={() => onSyncDevice(activeDevice.id)}
                className={`flex items-center gap-2 px-4 py-2 border text-xs font-mono rounded-xl transition-all duration-300 ${
                  activeDevice.syncStatus === 'syncing' ? 'cursor-not-allowed opacity-70 ' : 'hover:scale-105 '
                } ${
                  isLight 
                    ? 'bg-cyan-50 border-cyan-200 hover:border-cyan-400 text-cyan-700 hover:bg-cyan-100'
                    : 'bg-cyan-950/40 hover:bg-cyan-950/80 border-cyan-850/50 hover:border-cyan-700/60 text-cyan-400'
                }`}
                disabled={activeDevice.syncStatus === 'syncing'}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${activeDevice.syncStatus === 'syncing' ? 'animate-spin' : ''}`} />
                {activeDevice.syncStatus === 'syncing' ? 'SYNCHRONIZING...' : 'FORCE TELEMETRY SYNC'}
              </button>
            </div>

            {/* Core telemetry details specs */}
            {activeDevice.type === 'mobile' ? (
              <div className="space-y-6 my-4 flex-1 flex flex-col justify-between">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Left Column: ADB Wireless Connection */}
                  <div className="space-y-4">
                    <h3 className={`text-xs font-mono uppercase tracking-widest flex items-center gap-2 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                      <Wifi className="w-3.5 h-3.5 text-cyan-500" /> ADB Device Ecosystem
                    </h3>

                    <div className={`p-5 rounded-2xl border space-y-4 ${
                      isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                    }`}>
                      {/* Detected Real ADB Devices List */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-[10px] font-mono text-slate-500 uppercase flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" />
                            Detected ADB Devices ({realDevices.length})
                          </label>
                          <button
                            onClick={fetchRealADBDevices}
                            className="text-[9px] font-mono text-cyan-500 hover:text-cyan-400 flex items-center gap-0.5 cursor-pointer"
                          >
                            <RefreshCw className="w-2.5 h-2.5" /> REFRESH
                          </button>
                        </div>

                        {realDevices.length === 0 ? (
                          <div className="p-3 border border-dashed border-slate-800/60 rounded-xl text-center text-[10px] text-slate-500 font-mono">
                            No devices detected via USB or Wireless.
                            <div className="mt-1 text-[9px] text-slate-650">
                              Plug device in via USB and check if USB Debugging is active.
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-2 max-h-[140px] overflow-y-auto pr-1">
                            {realDevices.map((d) => {
                              const isSelected = selectedRealDevice === d.serial;
                              return (
                                <div
                                  key={d.serial}
                                  onClick={() => setSelectedRealDevice(d.serial)}
                                  className={`p-2.5 rounded-xl border transition-all cursor-pointer flex flex-col gap-1.5 ${
                                    isSelected
                                      ? (isLight ? 'bg-cyan-50/70 border-cyan-300' : 'bg-slate-900 border-cyan-800/60')
                                      : (isLight ? 'bg-white border-slate-200 hover:bg-slate-50' : 'bg-slate-950/40 border-slate-900 hover:bg-slate-900/20')
                                  }`}
                                >
                                  <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-1.5">
                                      <Smartphone className="w-3.5 h-3.5 text-cyan-400" />
                                      <span className="text-xs font-bold text-slate-200 truncate max-w-[120px]">
                                        {d.model}
                                      </span>
                                    </div>
                                    <span className={`text-[8px] font-mono uppercase px-1.5 py-0.5 rounded-full ${
                                      d.status === "device" ? "bg-emerald-950/30 text-emerald-450 border border-emerald-900/20" :
                                      "bg-amber-950/30 text-amber-400 border border-amber-900/20"
                                    }`}>
                                      {d.status}
                                    </span>
                                  </div>

                                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-500">
                                    <span className="truncate max-w-[130px]">{d.serial}</span>
                                    <span>{d.is_wireless ? "WIRELESS" : "USB"}</span>
                                  </div>

                                  {/* Device quick action toolbar */}
                                  <div className="flex justify-end gap-1.5 pt-1.5 border-t border-slate-800/10">
                                    {!d.is_wireless && d.status === "device" && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleAdbTcpIp(d.serial);
                                        }}
                                        className="px-2 py-0.5 rounded bg-cyan-600/15 hover:bg-cyan-600/25 border border-cyan-500/20 text-cyan-400 text-[8px] font-bold font-mono tracking-wider cursor-pointer"
                                        title="Enable Wireless TCP/IP mode so you can connect without a cable"
                                      >
                                        ENABLE WIRELESS
                                      </button>
                                    )}
                                    {d.is_wireless && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleAdbDisconnect(d.serial);
                                        }}
                                        className="px-2 py-0.5 rounded bg-rose-650/15 hover:bg-rose-650/25 border border-rose-500/20 text-rose-450 text-[8px] font-bold font-mono tracking-wider cursor-pointer"
                                      >
                                        DISCONNECT
                                      </button>
                                    )}
                                    {d.status === "device" && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setSelectedRealDevice(d.serial);
                                          handleAdbScrcpy();
                                        }}
                                        className="px-2 py-0.5 rounded bg-cyan-600 hover:bg-cyan-550 text-white text-[8px] font-bold font-mono tracking-wider cursor-pointer flex items-center gap-0.5"
                                      >
                                        <Play className="w-2.5 h-2.5 fill-white/10" /> MIRROR
                                      </button>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>

                      {/* Manual Connection Option */}
                      <div className="border-t border-slate-800/10 pt-3.5 space-y-3">
                        <span className="text-[9px] font-mono text-slate-500 uppercase block">Manual Wireless Connection</span>
                        
                        <div className="grid grid-cols-3 gap-3">
                          <div className="col-span-2">
                            <label className="text-[9px] font-mono text-slate-500 uppercase">Device IP Address</label>
                            <input
                              type="text"
                              value={adbIp}
                              onChange={(e) => setAdbIp(e.target.value)}
                              placeholder="192.168.1.100"
                              className={`w-full mt-1 px-3 py-1.5 rounded-xl text-xs font-mono border focus:outline-none transition-all ${
                                isLight 
                                  ? 'bg-white border-slate-200 focus:border-cyan-500 text-slate-900' 
                                  : 'bg-slate-950 border-slate-800 focus:border-cyan-600 text-slate-100'
                              }`}
                            />
                          </div>
                          <div>
                            <label className="text-[9px] font-mono text-slate-500 uppercase">Port</label>
                            <input
                              type="text"
                              value={adbPort}
                              onChange={(e) => setAdbPort(e.target.value)}
                              placeholder="5555"
                              className={`w-full mt-1 px-3 py-1.5 rounded-xl text-xs font-mono border focus:outline-none transition-all ${
                                isLight 
                                  ? 'bg-white border-slate-200 focus:border-cyan-500 text-slate-900' 
                                  : 'bg-slate-950 border-slate-800 focus:border-cyan-600 text-slate-100'
                              }`}
                            />
                          </div>
                        </div>

                        <div className="flex gap-3">
                          <button
                            onClick={handleAdbConnect}
                            disabled={isConnecting}
                            className={`flex-1 py-2.5 rounded-xl text-xs font-bold font-mono transition-all border cursor-pointer ${
                              isLight
                                ? 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300'
                                : 'bg-slate-900 hover:bg-slate-800 text-slate-200 border-slate-850'
                            }`}
                          >
                            {isConnecting ? "CONNECTING..." : "CONNECT WIRELESS"}
                          </button>
                          <button
                            onClick={handleAdbScrcpy}
                            className="px-3 py-2.5 bg-cyan-600 hover:bg-cyan-550 text-white rounded-xl text-xs font-bold font-mono flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-cyan-600/10 cursor-pointer"
                          >
                            <Play className="w-3.5 h-3.5" />
                            MIRROR
                          </button>
                          {onOpenMobileScreen && (
                            <button
                              onClick={onOpenMobileScreen}
                              className="px-3 py-2.5 bg-indigo-600 hover:bg-indigo-550 text-white rounded-xl text-xs font-bold font-mono flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-indigo-600/10 cursor-pointer"
                            >
                              <Smartphone className="w-3.5 h-3.5" />
                              FLOATING SCREEN
                            </button>
                          )}
                        </div>
                      </div>

                      {adbStatus && (
                        <div className={`p-2.5 rounded-xl border flex items-start gap-2 text-[10px] font-mono ${
                          adbStatus.includes("Failed") || adbStatus.includes("Error") || adbStatus.includes("failed") || adbStatus.includes("error")
                            ? (isLight ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-rose-950/20 border-rose-900/30 text-rose-450')
                            : (isLight ? 'bg-cyan-50 border-cyan-200 text-cyan-700' : 'bg-cyan-950/20 border-cyan-900/30 text-cyan-450')
                        }`}>
                          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                          <span>{adbStatus}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right Column: Device Hardware Remote Buttons */}
                  <div className="space-y-4">
                    <h3 className={`text-xs font-mono uppercase tracking-widest flex items-center gap-2 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                      <Terminal className="w-3.5 h-3.5 text-indigo-500" /> Device Input Control
                    </h3>

                    <div className={`p-5 rounded-2xl border ${
                      isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                    }`}>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => handleAdbControl("unlock")}
                          className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 transition-all hover:scale-102 ${
                            isLight 
                              ? 'bg-emerald-50 border-emerald-200 hover:bg-emerald-100 text-emerald-800' 
                              : 'bg-emerald-950/30 border-emerald-900/40 hover:bg-emerald-900/40 text-emerald-300'
                          }`}
                        >
                          <Power className="w-4 h-4 text-emerald-400" />
                          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold">Unlock Mobile</span>
                        </button>

                        <button
                          onClick={() => handleAdbControl("lock")}
                          className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 transition-all hover:scale-102 ${
                            isLight 
                              ? 'bg-rose-50 border-rose-200 hover:bg-rose-100 text-rose-800' 
                              : 'bg-rose-950/30 border-rose-900/40 hover:bg-rose-900/40 text-rose-400'
                          }`}
                        >
                          <Power className="w-4 h-4 text-rose-500" />
                          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold">Lock Mobile</span>
                        </button>
                        
                        <button
                          onClick={() => handleAdbControl("home")}
                          className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 transition-all hover:scale-102 ${
                            isLight 
                              ? 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800' 
                              : 'bg-slate-900/40 border-slate-900 hover:bg-slate-900/70 text-slate-200'
                          }`}
                        >
                          <Home className="w-4 h-4 text-cyan-500" />
                          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold">Home Screen</span>
                        </button>

                        <button
                          onClick={() => handleAdbControl("back")}
                          className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 transition-all hover:scale-102 ${
                            isLight 
                              ? 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800' 
                              : 'bg-slate-900/40 border-slate-900 hover:bg-slate-900/70 text-slate-200'
                          }`}
                        >
                          <ArrowLeft className="w-4 h-4 text-indigo-500" />
                          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold">Go Back</span>
                        </button>

                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => handleAdbControl("vol_up")}
                            className={`p-2 rounded-xl border flex flex-col items-center justify-center gap-1 transition-all hover:scale-102 ${
                              isLight 
                                ? 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800' 
                                : 'bg-slate-900/40 border-slate-900 hover:bg-slate-900/70 text-slate-200'
                            }`}
                          >
                            <Volume2 className="w-4 h-4 text-emerald-500" />
                            <span className="text-[9px] font-mono uppercase font-semibold">Vol +</span>
                          </button>
                          <button
                            onClick={() => handleAdbControl("vol_down")}
                            className={`p-2 rounded-xl border flex flex-col items-center justify-center gap-1 transition-all hover:scale-102 ${
                              isLight 
                                ? 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800' 
                                : 'bg-slate-900/40 border-slate-900 hover:bg-slate-900/70 text-slate-200'
                            }`}
                          >
                            <VolumeX className="w-4 h-4 text-slate-500" />
                            <span className="text-[9px] font-mono uppercase font-semibold">Vol -</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-4">
                {/* Left Details block: Hardware stats */}
                <div className="space-y-4">
                  <h3 className={`text-xs font-mono uppercase tracking-widest flex items-center gap-2 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                    <Activity className="w-3 h-3 text-cyan-500" /> System Hardware
                  </h3>

                  <div className={`space-y-3 border rounded-xl p-4 ${isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'}`}>
                    {/* CPU Meter */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-xs font-medium ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>Processor Utilization</span>
                        <span className="text-xs font-mono font-semibold text-cyan-500">{activeDevice.cpu}%</span>
                      </div>
                      <div className={`h-2 rounded-full overflow-hidden ${isLight ? 'bg-slate-200' : 'bg-slate-900'}`}>
                        <motion.div 
                          className="h-full bg-cyan-500 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${activeDevice.cpu}%` }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                      </div>
                    </div>

                    {/* RAM Meter */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-xs font-medium ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>Memory Allocation</span>
                        <span className="text-xs font-mono font-semibold text-indigo-500">{activeDevice.ram}%</span>
                      </div>
                      <div className={`h-2 rounded-full overflow-hidden ${isLight ? 'bg-slate-200' : 'bg-slate-900'}`}>
                        <motion.div 
                          className="h-full bg-indigo-500 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${activeDevice.ram}%` }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                      </div>
                    </div>

                    {/* Storage bar */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-xs font-medium ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>Durable Partition</span>
                        <span className={`text-xs font-mono font-semibold ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>{activeDevice.storage}</span>
                      </div>
                      <div className={`h-2 rounded-full overflow-hidden ${isLight ? 'bg-slate-200' : 'bg-slate-900'}`}>
                        <div className={`h-full rounded-full w-[68%] ${isLight ? 'bg-slate-400' : 'bg-slate-600'}`} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Details block: Node states */}
                <div className="space-y-4">
                  <h3 className={`text-xs font-mono uppercase tracking-widest flex items-center gap-2 ${isLight ? 'text-slate-500' : 'text-slate-450'}`}>
                    <Terminal className="w-3 h-3 text-indigo-500" /> Active Processes
                  </h3>

                  <div className={`space-y-3 border rounded-xl p-4 flex-1 ${isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'}`}>
                    {activeDevice.tasks.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-6 text-center">
                        <ShieldAlert className={`w-8 h-8 mb-1 ${isLight ? 'text-slate-400' : 'text-slate-600'}`} />
                        <p className={`text-xs font-mono ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>No background jobs active</p>
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {activeDevice.tasks.map((task, idx) => (
                          <div key={idx} className={`flex items-center justify-between text-xs border p-2.5 rounded-lg ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-slate-900'}`}>
                            <div className={`flex items-center gap-2 font-mono ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                              <span className="h-1.5 w-1.5 rounded-full bg-cyan-500 animate-pulse" />
                              {task}
                            </div>
                            
                            <button
                              onClick={() => onToggleTask(activeDevice.id, task)}
                              className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
                                isLight 
                                  ? 'text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 border-red-200'
                                  : 'text-red-400 hover:text-red-300 bg-red-950/30 hover:bg-red-900/30 border-red-900/40'
                              }`}
                            >
                              TERMINATE
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Quick Action Control Swatches */}
            <div className={`border-t pt-4 mt-2 ${isLight ? 'border-slate-200' : 'border-slate-900/80'}`}>
              <h3 className={`text-xs font-mono uppercase tracking-widest mb-3 flex items-center gap-2 ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
                <Sparkles className="w-3 h-3 text-cyan-500" /> Edge Agent Integrations
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className={`p-3 border rounded-xl flex flex-col gap-1 transition-colors cursor-pointer ${isLight ? 'bg-white border-slate-200 hover:border-slate-300 shadow-sm' : 'bg-slate-900/40 border-slate-900/80 hover:border-slate-800'}`}>
                  <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>WIFI NETWORK</span>
                  <span className={`text-xs font-medium ${isLight ? 'text-slate-800' : 'text-white'}`}>{activeDevice.network}</span>
                </div>
                
                <div className={`p-3 border rounded-xl flex flex-col gap-1 transition-colors cursor-pointer ${isLight ? 'bg-white border-slate-200 hover:border-slate-300 shadow-sm' : 'bg-slate-900/40 border-slate-900/80 hover:border-slate-800'}`}>
                  <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>BATTERY LEVEL</span>
                  <span className={`text-xs font-medium ${isLight ? 'text-slate-800' : 'text-white'}`}>{activeDevice.battery}% {activeDevice.isCharging ? "(Charging)" : ""}</span>
                </div>

                <div className={`p-3 border rounded-xl flex flex-col gap-1 transition-colors cursor-pointer ${isLight ? 'bg-white border-slate-200 hover:border-slate-300 shadow-sm' : 'bg-slate-900/40 border-slate-900/80 hover:border-slate-800'}`}>
                  <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>ENCRYPTION ENGINE</span>
                  <span className="text-xs font-medium text-emerald-500">LUKS2 AES-256</span>
                </div>

                <div className={`p-3 border rounded-xl flex flex-col gap-1 transition-colors cursor-pointer ${isLight ? 'bg-white border-slate-200 hover:border-slate-300 shadow-sm' : 'bg-slate-900/40 border-slate-900/80 hover:border-slate-800'}`}>
                  <span className={`text-[10px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>SYNC CHANNELS</span>
                  <span className={`text-xs font-medium ${isLight ? 'text-slate-800' : 'text-white'}`}>TLS WebSocket</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center flex-1 text-center">
            <Monitor className={`w-12 h-12 mb-2 ${isLight ? 'text-slate-300' : 'text-slate-700'}`} />
            <p className={`text-sm ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>No device selected. Click a device from the left panel to analyze.</p>
          </div>
        )}
      </div>
    </div>
  );
}
