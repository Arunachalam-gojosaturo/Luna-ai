import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { GitBranch, FolderGit, Terminal, Code, Cpu, RefreshCw, Send, Play, CheckCircle2, AlertTriangle, Sparkles } from "lucide-react";
import { GitHubRepo, LogMessage } from "../types";

interface DeveloperWorkspaceProps {
  repos: GitHubRepo[];
  terminalLogs: LogMessage[];
  onTriggerBuild: (repoName: string) => void;
  onRunTerminalCommand: (command: string) => void;
  onGenerateCode: (prompt: string, repoName: string) => void;
  onAddRepo?: (repo: GitHubRepo) => void;
  isGeneratingCode: boolean;
  isLight?: boolean;
}

export default function DeveloperWorkspace({
  repos,
  terminalLogs,
  onTriggerBuild,
  onRunTerminalCommand,
  onGenerateCode,
  onAddRepo,
  isGeneratingCode,
  isLight = false
}: DeveloperWorkspaceProps) {
  const [selectedRepo, setSelectedRepo] = useState<string>(repos[0]?.name || "");
  const [terminalInput, setTerminalInput] = useState<string>("");
  const [coderPrompt, setCoderPrompt] = useState<string>("");
  
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal to bottom
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [terminalLogs]);

  const activeRepo = repos.find(r => r.name === selectedRepo) || repos[0];

  const handleTerminalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!terminalInput.trim()) return;
    onRunTerminalCommand(terminalInput);
    setTerminalInput("");
  };

  const handleGenerateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!coderPrompt.trim()) return;
    onGenerateCode(coderPrompt, selectedRepo);
    setCoderPrompt("");
  };

  const getStatusIcon = (status: 'success' | 'failed' | 'building' | 'none') => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'building':
        return <RefreshCw className="w-4 h-4 text-amber-500 animate-spin" />;
      default:
        return <FolderGit className={`w-4 h-4 ${isLight ? 'text-slate-500' : 'text-slate-400'}`} />;
    }
  };

  const getLogColor = (type: LogMessage['type']) => {
    switch (type) {
      case 'success': return isLight ? 'text-emerald-600' : 'text-emerald-400';
      case 'warning': return isLight ? 'text-amber-600' : 'text-amber-400';
      case 'error': return isLight ? 'text-red-600 font-bold' : 'text-red-400 font-bold';
      case 'system': return isLight ? 'text-purple-600 font-medium' : 'text-purple-400 font-medium';
      case 'output': return isLight ? 'text-slate-600' : 'text-slate-300';
      case 'info':
      default:
        return isLight ? 'text-cyan-600' : 'text-cyan-400';
    }
  };

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-12 gap-6 h-full ${isLight ? 'text-slate-800' : 'text-slate-100'}`} id="developer-workspace-container">
      
      {/* Repositories Sidebar (Left - span 4) */}
      <div className="lg:col-span-4 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className={`text-md font-semibold font-display flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
            <FolderGit className="w-4 h-4 text-cyan-500" />
            Active Repositories
          </h2>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono px-2 py-0.5 border rounded-full ${isLight ? 'bg-slate-100 border-slate-200 text-slate-500' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
              GITHUB SOURCE
            </span>
            <label className={`cursor-pointer text-[10px] font-bold px-2 py-0.5 rounded-full border transition-all ${isLight ? 'bg-cyan-50 border-cyan-200 text-cyan-600 hover:bg-cyan-100' : 'bg-cyan-900/40 border-cyan-800 text-cyan-400 hover:bg-cyan-900/60'}`}>
              + ADD PROJECT
              <input 
                type="file" 
                // @ts-ignore
                webkitdirectory="true" 
                directory="true"
                className="hidden" 
                onChange={(e) => {
                  const files = e.target.files;
                  if (files && files.length > 0 && onAddRepo) {
                    const path = files[0].webkitRelativePath;
                    const folderName = path.split('/')[0] || "New Project";
                    onAddRepo({
                      name: folderName,
                      description: `Local project loaded from ${folderName}`,
                      branch: "main",
                      stars: 0,
                      languages: ["Unknown"],
                      buildStatus: "none",
                      lastCommit: "init"
                    });
                  }
                }} 
              />
            </label>
          </div>
        </div>

        <div className="space-y-2 flex-1 overflow-y-auto pr-1">
          {repos.map(repo => {
            const isSelected = repo.name === selectedRepo;
            return (
              <div
                key={repo.name}
                onClick={() => setSelectedRepo(repo.name)}
                className={`p-3.5 rounded-xl border transition-all duration-200 cursor-pointer relative ${
                  isSelected
                    ? (isLight ? 'bg-white/70 border-cyan-200 shadow-[0_4px_20px_rgba(6,182,212,0.1)]' : 'bg-slate-900/60 border-slate-800 shadow-[0_4px_20px_rgba(6,182,212,0.06)]')
                    : (isLight ? 'bg-white/40 border-slate-200 hover:bg-white/60 hover:border-slate-300' : 'bg-slate-950/40 border-slate-900/60 hover:bg-slate-900/20 hover:border-slate-850')
                }`}
              >
                {isSelected && (
                  <div className="absolute inset-y-3 left-0 w-1 bg-cyan-400 rounded-r-md" />
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    {getStatusIcon(repo.buildStatus)}
                    <h3 className={`text-sm font-medium ${isLight ? 'text-slate-800' : 'text-white'}`}>{repo.name}</h3>
                  </div>
                  <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${isLight ? 'bg-slate-50 border-slate-200 text-slate-500' : 'bg-slate-900 border-slate-850 text-slate-500'}`}>
                    {repo.branch}
                  </span>
                </div>

                <p className={`text-xs mt-1.5 truncate leading-relaxed ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  {repo.description}
                </p>

                <div className={`flex items-center justify-between mt-3 pt-2 border-t text-[10px] font-mono ${isLight ? 'border-slate-200 text-slate-500' : 'border-slate-900/50 text-slate-500'}`}>
                  <span className="flex items-center gap-1">
                    <GitBranch className="w-3 h-3 text-cyan-500" />
                    {repo.stars} stars
                  </span>
                  <span>
                    Commit: {repo.lastCommit}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Workspace Frame (Middle & Right - span 8) */}
      <div className="lg:col-span-8 flex flex-col gap-6">
        
        {/* Terminal and Build Controller - Always keep terminal styling somewhat terminal-like but adapt slightly for light mode */}
        <div className={`border rounded-2xl overflow-hidden flex flex-col h-[320px] shadow-2xl relative font-mono ${isLight ? 'bg-white border-slate-200' : 'bg-slate-950/80 border-slate-900'}`}>
          
          {/* Terminal Titlebar */}
          <div className={`border-b px-4 py-2.5 flex items-center justify-between ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-900/60 border-slate-900/80'}`}>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/80" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className={`text-xs ml-2 flex items-center gap-1.5 font-mono ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                <Terminal className="w-3.5 h-3.5 text-cyan-500" />
                bash // lunasandbox@node-cloud-1
              </span>
            </div>

            {activeRepo && (
              <button
                onClick={() => onTriggerBuild(activeRepo.name)}
                className={`flex items-center gap-1.5 px-3 py-1 border text-[10px] rounded-lg transition-colors cursor-pointer ${isLight ? 'bg-cyan-50 hover:bg-cyan-100 border-cyan-200 text-cyan-700' : 'bg-cyan-950/50 hover:bg-cyan-950/90 border-cyan-900/50 text-cyan-400'}`}
              >
                <RefreshCw className="w-3 h-3" />
                COMPILE WORKSPACE
              </button>
            )}
          </div>

          {/* Terminal Outputs */}
          <div className={`p-4 flex-1 overflow-y-auto space-y-2 text-xs font-mono leading-relaxed ${isLight ? 'bg-white' : 'bg-slate-950/40'}`}>
            {terminalLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className={`select-none text-[10px] pt-0.5 ${isLight ? 'text-slate-400' : 'text-slate-600'}`}>{log.timestamp}</span>
                <span className={`${getLogColor(log.type)}`}>
                  {log.text}
                </span>
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>

          {/* Terminal Input Bar */}
          <form onSubmit={handleTerminalSubmit} className={`border-t px-4 py-2 flex items-center gap-2 ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-900/40 border-slate-900'}`}>
            <span className="text-cyan-500 font-bold select-none">$</span>
            <input
              type="text"
              value={terminalInput}
              onChange={(e) => setTerminalInput(e.target.value)}
              placeholder="Type system commands... (e.g., 'npm test', 'tsc', 'luna doctor', 'git diff')"
              className={`bg-transparent border-none outline-none flex-1 text-xs font-mono ${isLight ? 'text-slate-800 placeholder:text-slate-400' : 'text-slate-100 placeholder:text-slate-600'}`}
            />
            <button type="submit" className={`p-1 transition-colors cursor-pointer ${isLight ? 'text-cyan-600 hover:text-cyan-500' : 'text-cyan-400 hover:text-cyan-300'}`}>
              <Play className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

        {/* AI Coding Assistant Container */}
        <div className={`border rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex flex-col gap-4 ${isLight ? 'bg-white/60 border-slate-200/60 shadow-lg' : 'bg-slate-950/60 border-slate-900'}`}>
          <div className={`absolute top-0 right-0 w-32 h-32 blur-2xl pointer-events-none ${isLight ? 'bg-purple-500/10' : 'bg-purple-500/5'}`} />
          
          <div className="flex items-center justify-between z-10">
            <div>
              <h3 className={`text-sm font-semibold font-display flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                <Code className="w-4 h-4 text-purple-500 animate-pulse" />
                Copilot Code Architect
              </h3>
              <p className={`text-xs mt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                Targeting: <span className="text-cyan-500 font-mono text-[11px]">{activeRepo?.name || "No Repo Selected"}</span>
              </p>
            </div>

            <span className={`text-[10px] font-mono border px-2.5 py-0.5 rounded-full flex items-center gap-1.5 ${isLight ? 'bg-purple-50 border-purple-200 text-purple-700' : 'bg-purple-950/40 border-purple-900/60 text-purple-400'}`}>
              <Sparkles className="w-3 h-3 text-purple-500 animate-pulse" />
              GEMINI-3.5-FLASH POWERED
            </span>
          </div>

          <form onSubmit={handleGenerateSubmit} className="flex gap-2.5 z-10">
            <input
              type="text"
              value={coderPrompt}
              onChange={(e) => setCoderPrompt(e.target.value)}
              placeholder="e.g., 'Create a Dockerfile', 'Write a test suite for auth routing', 'Refactor DB connectors'..."
              className={`flex-1 border rounded-xl px-4 py-2.5 text-xs outline-none transition-all ${isLight ? 'bg-white/80 border-slate-200 hover:border-slate-300 focus:border-purple-400 text-slate-800 placeholder:text-slate-400' : 'bg-slate-900/80 border-slate-850 hover:border-slate-800 focus:border-purple-800 text-slate-200 placeholder:text-slate-500'}`}
              disabled={isGeneratingCode}
            />
            
            <button
              type="submit"
              disabled={isGeneratingCode || !coderPrompt.trim()}
              className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-slate-400 disabled:to-slate-400 dark:disabled:from-slate-900 dark:disabled:to-slate-900 disabled:text-slate-200 dark:disabled:text-slate-600 disabled:cursor-not-allowed text-white font-semibold text-xs rounded-xl flex items-center gap-1.5 transition-all shadow-lg shadow-purple-500/10 cursor-pointer"
            >
              {isGeneratingCode ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>ANALYZING AST...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>GENERATE</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
