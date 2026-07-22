export type CoreState = 'Idle' | 'Listening' | 'Thinking' | 'Speaking' | 'Executing' | 'Warning' | 'Offline' | 'Error';

export type ActiveView = 'home' | 'voice' | 'projects' | 'devices' | 'developer' | 'analytics' | 'chat' | 'settings';

export interface DeviceTelemetry {
  id: string;
  name: string;
  type: 'mobile' | 'workstation' | 'desktop';
  battery: number;
  isCharging: boolean;
  network: string;
  syncStatus: 'synced' | 'syncing' | 'offline';
  cpu: number;
  ram: number;
  storage: string;
  tasks: string[];
  osVersion: string;
}

export interface ActivityEvent {
  id: string;
  text: string;
  type: 'task' | 'action' | 'memory' | 'device' | 'voice' | 'system';
  timestamp: string;
}

export interface TTSSettings {
  provider: 'edge' | 'elevenlabs';
  voiceId: string;
  speed: number;
  pitch: number;
  elevenLabsApiKey: string;
}

export interface SystemMetrics {
  cpuUsage: number;
  ramUsage: number;
  neuralLoad: number;
  networkSpeed: string;
  uptime: string;
}

export interface SystemGoal {
  id: string;
  title: string;
  category: 'Intelligence' | 'Ecosystem' | 'Health' | 'Workspace';
  current: string;
  target: string;
  progress: number; // 0 to 100
}

export interface HealthData {
  steps: number;
  stepGoal: number;
  calories: number;
  calorieGoal: number;
  distance: number; // in miles
  distanceGoal: number;
  sleepHours: number;
  sleepGoal: number;
  heartRate: number;
}

export interface GitHubRepo {
  name: string;
  description: string;
  branch: string;
  stars: number;
  languages: string[];
  buildStatus: 'success' | 'failed' | 'building' | 'none';
  lastCommit: string;
}

export interface LogMessage {
  text: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'system' | 'output';
  timestamp: string;
}
