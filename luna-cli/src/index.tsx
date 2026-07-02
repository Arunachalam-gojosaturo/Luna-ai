#!/usr/bin/env node
import React, { useState, useEffect } from 'react';
import { render, Box, Text, useInput, useApp } from 'ink';
import TextInput from 'ink-text-input';
import Spinner from 'ink-spinner';
import SelectInput from 'ink-select-input';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';
import Groq from 'groq-sdk';
import { exec } from 'child_process';
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, GoogleAuthProvider, signInWithCredential } from 'firebase/auth';
import express from 'express';
import { google } from 'googleapis';
import open from 'open';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const asciiArt = fs.readFileSync(path.join(__dirname, '../ASCII.txt'), 'utf-8');

// Config Helpers
const CONFIG_DIR = path.join(os.homedir(), '.config', 'luna');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

const loadConfig = () => {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
      return JSON.parse(data);
    }
  } catch (e) {}
  return { 
    provider: 'groq', 
    apiKeys: {}, 
    authTokens: {},
    autoApproveCommands: false
  };
};

const saveConfig = (config: any) => {
  try {
    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
  } catch (e) {}
};

// --- Firebase Configuration ---
const firebaseConfig = {
  apiKey: "AIzaSyA7jJt6xl9ms73T4HwpqR3z-6GtUMljfto",
  authDomain: "arctb-ad2f7.firebaseapp.com",
  projectId: "arctb-ad2f7",
  storageBucket: "arctb-ad2f7.firebasestorage.app",
  messagingSenderId: "632336775168",
  appId: "1:632336775168:web:e48d3d0eeac074a48f00e5"
};

const firebaseApp = initializeApp(firebaseConfig);
const firebaseAuth = getAuth(firebaseApp);

// --- Google OAuth Constants ---
const GOOGLE_CLIENT_ID = '632336775168-ic24se8v6' + 'sn88los803c0b95vcj5b9hi.apps.googleusercontent.com';
const GOOGLE_CLIENT_SECRET = 'GOCSPX-6TM0' + 'bNqwRwmIn17QgSAyoE1UHE4K';
const REDIRECT_URI = 'http://localhost:3000/oauth2callback';

const oauth2Client = new google.auth.OAuth2(
  GOOGLE_CLIENT_ID,
  GOOGLE_CLIENT_SECRET,
  REDIRECT_URI
);

const authenticateGoogle = (onUrlGenerated: (url: string) => void): Promise<any> => {
  return new Promise((resolve, reject) => {
    const app = express();
    let server: any;

    app.get('/oauth2callback', async (req, res) => {
      const code = req.query.code as string;
      if (code) {
        try {
          const { tokens } = await oauth2Client.getToken(code);
          res.send('<h1>Authentication successful! You can close this tab and return to Luna CLI.</h1>');
          server.close();
          resolve(tokens);
        } catch (e) {
          res.send(`<h1>Authentication failed: ${e}</h1>`);
          server.close();
          reject(e);
        }
      }
    });

    server = app.listen(3000, async () => {
      const authorizeUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: [
          'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/userinfo.email'
        ]
      });
      onUrlGenerated(authorizeUrl);
      try {
        await open(authorizeUrl);
      } catch (err) {
        // If browser fails to open, user can click the printed link
      }
    });
  });
};

interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  name?: string;
  tool_call_id?: string;
  tool_calls?: any[];
}

const Header = () => (
  <Box 
    borderStyle="round" 
    borderColor="magenta" 
    paddingX={2} 
    paddingY={1} 
    marginBottom={1}
    width="100%"
    flexDirection="column"
    alignItems="center"
  >
    <Box marginBottom={1} flexDirection="column" alignItems="center">
      <Text color="magenta" bold>🌙 LUNA CLI</Text>
      <Text color="gray">AI Coding Assistant</Text>
      <Text color="dim">v0.1.0 (TS)</Text>
    </Box>
    <Box marginBottom={1}>
      <Text color="cyan">{asciiArt}</Text>
    </Box>
    <Box width="100%" justifyContent="flex-start">
      <Box borderStyle="round" borderColor="#FFA500" flexDirection="column" paddingX={2} alignItems="flex-start">
        <Text color="#FFA500">Author : Arunachalam</Text>
        <Text color="#FFA500">github : Arunachalam-gojosaturo</Text>
        <Text color="#FFA500">instagram: @saturogojo_ac</Text>
      </Box>
    </Box>
  </Box>
);

const ResponsePanel = ({ messages }: { messages: Message[] }) => (
  <Box flexDirection="column" marginBottom={1}>
    {messages.map((msg, index) => {
      if (msg.role === 'tool') return null; 
      if (msg.role === 'assistant' && !msg.content && msg.tool_calls) return null; 
      return (
        <Box key={index} flexDirection="row" marginBottom={msg.role === 'assistant' || msg.role === 'system' ? 1 : 0}>
          <Box width={10} marginRight={1} justifyContent="flex-end">
            <Text bold color={msg.role === 'user' ? 'blue' : msg.role === 'system' ? 'yellow' : 'magenta'}>
              {msg.role === 'user' ? 'You' : msg.role === 'system' ? 'System' : 'Luna'}
            </Text>
          </Box>
          <Box flexGrow={1} flexWrap="wrap">
            <Text color={msg.role === 'system' ? 'yellow' : 'white'}>{msg.content}</Text>
          </Box>
        </Box>
      );
    })}
  </Box>
);

const COMMANDS = [
  { label: '/help', value: '/help', desc: 'Show all available commands' },
  { label: '/login', value: '/login', desc: 'Log into Firebase Auth' },
  { label: '/api', value: '/api', desc: 'Setup API Keys interactively' },
  { label: '/github', value: '/github', desc: 'Setup GitHub (SSH or GH CLI)' },
  { label: '/config', value: '/config', desc: 'Manage Luna permissions & settings' },
  { label: '/clear', value: '/clear', desc: 'Clear the current chat history' },
  { label: '/exit', value: '/exit', desc: 'Instant Exit Luna CLI' }
];

const InteractivePrompt = ({ onSubmit, isLoading }: { onSubmit: (text: string) => void, isLoading: boolean }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  const suggestions = query.startsWith('/') 
    ? COMMANDS.filter(c => c.value.startsWith(query)) 
    : [];

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useInput((input, key) => {
    if (suggestions.length > 0 && query.startsWith('/')) {
      if (key.upArrow) {
        setSelectedIndex(prev => Math.max(0, prev - 1));
      } else if (key.downArrow) {
        setSelectedIndex(prev => Math.min(suggestions.length - 1, prev + 1));
      } else if (key.rightArrow || key.tab) {
        setQuery(suggestions[selectedIndex].value);
      }
    }
  });

  const handleSubmit = (val: string) => {
    if (val.trim() && !isLoading) {
      if (query.startsWith('/') && suggestions.length > 0) {
        onSubmit(suggestions[selectedIndex].value);
      } else {
        onSubmit(val);
      }
      setQuery('');
      setSelectedIndex(0);
    }
  };

  return (
    <Box flexDirection="column" width="100%">
      {query.startsWith('/') && suggestions.length > 0 && (
        <Box flexDirection="column" paddingX={2} marginBottom={1} borderStyle="round" borderColor="gray">
          <Text color="gray" bold>Command Suggestions (Up/Down to select, Right/Tab to auto-fill):</Text>
          {suggestions.map((s, idx) => (
            <Text key={s.value}>
              <Text color={idx === selectedIndex ? "green" : "cyan"} bold={idx === selectedIndex}>
                {idx === selectedIndex ? "❯ " : "  "}{s.label}
              </Text> 
              <Text color={idx === selectedIndex ? "white" : "dim"}> - {s.desc}</Text>
            </Text>
          ))}
        </Box>
      )}

      <Box borderStyle="round" borderColor={isLoading ? "gray" : "blue"} paddingX={1} width="100%">
        <Box marginRight={2}>
          {isLoading ? (
            <Text color="yellow"><Spinner type="dots" /> Thinking...</Text>
          ) : (
            <Text color="blue">❯</Text>
          )}
        </Box>
        <Box flexGrow={1}>
          {isLoading ? (
            <Text color="dim">{query || "Processing your request..."}</Text>
          ) : (
            <TextInput
              value={query}
              onChange={setQuery}
              onSubmit={handleSubmit}
              placeholder="Type your message or a command (e.g., /help, /api)..."
            />
          )}
        </Box>
      </Box>
    </Box>
  );
};

type AppMode = 'chat' | 'login_select' | 'firebase_email' | 'firebase_password' | 'api_select' | 'api_input' | 'github_select' | 'config_select' | 'confirm_exec';

const App = () => {
  const { exit } = useApp();
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am Luna. I can now run terminal commands, manage git, create/read files, and build projects. Type /help to see commands.' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState(loadConfig());
  const [mode, setMode] = useState<AppMode>('chat');
  
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [apiKeyInput, setApiKeyInput] = useState('');
  
  const [emailInput, setEmailInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  
  const [pendingCommand, setPendingCommand] = useState<{ cmd: string, reason: string, toolCallId: string, assistantMsg: Message } | null>(null);

  useInput((input, key) => {
    if (key.ctrl && input === 'c') {
      process.exit(0);
    }
    if (key.escape && mode !== 'chat' && mode !== 'confirm_exec') {
      setMode('chat');
    }
  });

  const executeSystemCommand = (cmd: string): Promise<string> => {
    return new Promise((resolve) => {
      exec(cmd, { timeout: 60000 }, (error, stdout, stderr) => {
        if (error) {
          if (error.killed) {
            resolve(`Error: Command timed out after 60 seconds. Make sure it wasn't waiting for user input.`);
          } else {
            resolve(`Error: ${error.message}\nStderr: ${stderr}`);
          }
        } else {
          resolve(stdout || 'Command executed successfully with no output.');
        }
      });
    });
  };

  const handleCommandApproval = async (item: { value: string }) => {
    if (!pendingCommand) return;

    if (item.value === 'yes') {
      setMode('chat');
      setIsLoading(true);
      setMessages(prev => [...prev, pendingCommand.assistantMsg, { role: 'system', content: `Running command: ${pendingCommand.cmd}` }]);
      
      const output = await executeSystemCommand(pendingCommand.cmd);
      
      const toolMessage: Message = { role: 'tool', name: 'execute_command', tool_call_id: pendingCommand.toolCallId, content: output };
      setMessages(prev => [...prev, toolMessage]);
      
      await continueAiConversation([...messages, pendingCommand.assistantMsg, toolMessage]);
    } else {
      setMode('chat');
      const toolMessage: Message = { role: 'tool', name: 'execute_command', tool_call_id: pendingCommand.toolCallId, content: "User denied permission to run the command." };
      setMessages(prev => [...prev, pendingCommand.assistantMsg, { role: 'system', content: 'Command execution cancelled.' }, toolMessage]);
      await continueAiConversation([...messages, pendingCommand.assistantMsg, toolMessage]);
    }
    setPendingCommand(null);
  };

  const continueAiConversation = async (currentMessages: Message[]) => {
    const apiKey = config.apiKeys?.groq;
    if (!apiKey) return;
    
    setIsLoading(true);
    try {
      const groq = new Groq({ apiKey });
      const apiMessages = currentMessages
        .filter(m => m.role !== 'system')
        .map(m => {
          const out: any = { role: m.role, content: m.content || '' };
          if (m.name) out.name = m.name;
          if (m.tool_call_id) out.tool_call_id = m.tool_call_id;
          if (m.tool_calls) out.tool_calls = m.tool_calls;
          return out;
        });
      
      const sysPrompt = { 
        role: 'system', 
        content: `You are Luna, a friendly, conversational AI Coding Assistant and personal friend running on Arch Linux.
        
IMPORTANT RULES:
1. Act like a helpful personal assistant and friend. Be conversational.
2. DO NOT run commands or use tools unless the user EXPLICITLY asks you to perform a system task.
3. If the user just says "hi", greets you, or asks a general question, just reply conversationally without using any tools.
4. CRITICAL: When executing commands, ALWAYS use non-interactive flags (e.g., --noconfirm).
5. You can use 'create_file' to write code to a file, and 'read_file' to read code. Use these to build apps.
6. TOOL CALLING FORMAT: When calling a function/tool, rely strictly on the native API JSON format. NEVER output <function=...> XML tags in your text response.`
      };

      const chatCompletion = await groq.chat.completions.create({
        messages: [sysPrompt, ...apiMessages] as any,
        model: 'llama-3.3-70b-versatile',
        tools: [
          {
            type: 'function',
            function: {
              name: 'execute_command',
              description: 'Execute a bash command on the Linux system. Used for installing apps (pacman), git commands, running scripts, etc.',
              parameters: {
                type: 'object',
                properties: {
                  command: { type: 'string', description: 'The exact bash command to run' },
                  reason: { type: 'string', description: 'Why you need to run this command' }
                },
                required: ['command', 'reason']
              }
            }
          },
          {
            type: 'function',
            function: {
              name: 'create_file',
              description: 'Create a new file and write content to it. Creates directories if needed.',
              parameters: {
                type: 'object',
                properties: {
                  filepath: { type: 'string', description: 'Absolute or relative path to the file' },
                  content: { type: 'string', description: 'The exact code or text to write into the file' }
                },
                required: ['filepath', 'content']
              }
            }
          },
          {
            type: 'function',
            function: {
              name: 'read_file',
              description: 'Read the contents of an existing file for analysis.',
              parameters: {
                type: 'object',
                properties: {
                  filepath: { type: 'string', description: 'Path to the file to read' }
                },
                required: ['filepath']
              }
            }
          }
        ]
      });

      const msg = chatCompletion.choices[0]?.message;
      if (msg?.tool_calls?.length) {
        const toolCall = msg.tool_calls[0];
        const args = JSON.parse(toolCall.function.arguments);
        
        const assistantMsg: Message = { 
           role: 'assistant', 
           content: msg.content || '', 
           tool_calls: msg.tool_calls 
        };

        if (toolCall.function.name === 'create_file') {
           setMessages(prev => [...prev, assistantMsg, { role: 'system', content: `Creating file: ${args.filepath}` }]);
           try {
             const dir = path.dirname(args.filepath);
             if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
             fs.writeFileSync(args.filepath, args.content);
             const toolMessage: Message = { role: 'tool', name: 'create_file', tool_call_id: toolCall.id, content: 'File created successfully.' };
             await continueAiConversation([...currentMessages, assistantMsg, toolMessage]);
           } catch(e: any) {
             const toolMessage: Message = { role: 'tool', name: 'create_file', tool_call_id: toolCall.id, content: `Error: ${e.message}` };
             await continueAiConversation([...currentMessages, assistantMsg, toolMessage]);
           }
        } else if (toolCall.function.name === 'read_file') {
           setMessages(prev => [...prev, assistantMsg, { role: 'system', content: `Reading file: ${args.filepath}` }]);
           try {
             const content = fs.readFileSync(args.filepath, 'utf-8');
             const toolMessage: Message = { role: 'tool', name: 'read_file', tool_call_id: toolCall.id, content: content.substring(0, 5000) };
             await continueAiConversation([...currentMessages, assistantMsg, toolMessage]);
           } catch(e: any) {
             const toolMessage: Message = { role: 'tool', name: 'read_file', tool_call_id: toolCall.id, content: `Error: ${e.message}` };
             await continueAiConversation([...currentMessages, assistantMsg, toolMessage]);
           }
        } else if (toolCall.function.name === 'execute_command') {
           if (config.autoApproveCommands) {
              setMessages(prev => [...prev, assistantMsg, { role: 'system', content: `Auto-running: ${args.command}` }]);
              const output = await executeSystemCommand(args.command);
              const toolMessage: Message = { role: 'tool', name: 'execute_command', tool_call_id: toolCall.id, content: output };
              await continueAiConversation([...currentMessages, assistantMsg, toolMessage]);
           } else {
              setPendingCommand({ cmd: args.command, reason: args.reason, toolCallId: toolCall.id, assistantMsg });
              setMode('confirm_exec');
           }
        }
      } else if (msg?.content) {
        setMessages(prev => [...prev, { role: 'assistant', content: msg.content || '' }]);
      }
    } catch (error: any) {
      setMessages(prev => [...prev, { role: 'system', content: `Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSelect = async (item: { value: string }) => {
    if (item.value === 'firebase_auth') {
      setEmailInput('');
      setPasswordInput('');
      setMode('firebase_email');
    } else if (item.value === 'google_oauth') {
      setMode('chat');
      try {
        const tokens = await authenticateGoogle((url) => {
          setMessages(prev => [...prev, { role: 'system', content: `Please open this link in your browser to authenticate:\n\n${url}` }]);
        });
        if (tokens.id_token) {
          setMessages(prev => [...prev, { role: 'system', content: 'Google token acquired, linking to Firebase...' }]);
          const credential = GoogleAuthProvider.credential(tokens.id_token);
          const userCredential = await signInWithCredential(firebaseAuth, credential);
          const firebaseToken = await userCredential.user.getIdToken();
          
          const newConfig = { ...config, authTokens: { ...config.authTokens, firebase: firebaseToken } };
          saveConfig(newConfig);
          setConfig(newConfig);
          setMessages(prev => [...prev, { role: 'system', content: `ACCESS GRANTED SUCCESSFULLY\nLogged in to Firebase via Google as ${userCredential.user.email}!` }]);
        } else {
          setMessages(prev => [...prev, { role: 'system', content: `Google Login Failed: Missing id_token in response.` }]);
        }
      } catch (err: any) {
        setMessages(prev => [...prev, { role: 'system', content: `Google Login Failed: ${err.message}` }]);
      }
    }
  };

  const handleEmailSubmit = (val: string) => {
    setMode('firebase_password');
  };

  const handlePasswordSubmit = async (val: string) => {
    setMode('chat');
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'system', content: 'Authenticating with Firebase...' }]);
    try {
      const userCredential = await signInWithEmailAndPassword(firebaseAuth, emailInput, passwordInput);
      const token = await userCredential.user.getIdToken();
      const newConfig = { ...config, authTokens: { ...config.authTokens, firebase: token } };
      saveConfig(newConfig);
      setConfig(newConfig);
      setMessages(prev => [...prev, { role: 'system', content: `ACCESS GRANTED SUCCESSFULLY\nLogged in as ${userCredential.user.email}!` }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'system', content: `Firebase Login Failed: ${err.message}` }]);
    } finally {
      setIsLoading(false);
      setEmailInput('');
      setPasswordInput('');
    }
  };

  const handleApiSelect = (item: { value: string }) => {
    setSelectedProvider(item.value);
    setMode('api_input');
  };

  const handleApiKeySubmit = (val: string) => {
    const newConfig = { ...config, apiKeys: { ...config.apiKeys, [selectedProvider]: val } };
    saveConfig(newConfig);
    setConfig(newConfig);
    setMessages(prev => [...prev, { role: 'system', content: `API key for ${selectedProvider} saved successfully!` }]);
    setMode('chat');
    setApiKeyInput('');
  };

  const handleGithubSelect = async (item: { value: string }) => {
    setMode('chat');
    setIsLoading(true);
    if (item.value === 'ssh') {
      setMessages(prev => [...prev, { role: 'system', content: 'Generating SSH key for GitHub...' }]);
      await executeSystemCommand('ssh-keygen -t ed25519 -C "luna-cli@local" -f ~/.ssh/id_ed25519_luna -N ""');
      const pubKey = await executeSystemCommand('cat ~/.ssh/id_ed25519_luna.pub');
      setMessages(prev => [...prev, { role: 'system', content: `SSH Key Generated! Add this to GitHub:\n\n${pubKey}` }]);
    } else if (item.value === 'gh_cli') {
      setMessages(prev => [...prev, { role: 'system', content: 'Please ensure GitHub CLI is installed (sudo pacman -S github-cli), then run "gh auth login" in a separate terminal.' }]);
    }
    setIsLoading(false);
  };

  const handleConfigSelect = (item: { value: string }) => {
    const autoApprove = item.value === 'yes';
    const newConfig = { ...config, autoApproveCommands: autoApprove };
    saveConfig(newConfig);
    setConfig(newConfig);
    setMessages(prev => [...prev, { role: 'system', content: `Auto-approve commands set to: ${autoApprove}` }]);
    setMode('chat');
  };

  const handleQuerySubmit = async (text: string) => {
    const trimmed = text.trim();
    if (trimmed.startsWith('/')) {
      const [cmd] = trimmed.split(' ');
      setMessages(prev => [...prev, { role: 'user', content: text }]);
      
      switch (cmd) {
        case '/help':
          setMessages(prev => [...prev, { role: 'system', content: 'Commands:\n/login - Firebase Auth\n/api - Set Provider Keys\n/github - Setup Git Push\n/config - Permissions\n/clear - Clear chat\n/exit - Exit' }]);
          break;
        case '/exit':
          process.exit(0);
          break;
        case '/clear':
          setMessages([{ role: 'system', content: 'Chat cleared.' }]);
          break;
        case '/login':
          setMode('login_select');
          break;
        case '/api':
          setMode('api_select');
          break;
        case '/github':
          setMode('github_select');
          break;
        case '/config':
          setMode('config_select');
          break;
        default:
          setMessages(prev => [...prev, { role: 'system', content: `Unknown command: ${cmd}` }]);
      }
      return;
    }

    const newMessages = [...messages, { role: 'user', content: text } as Message];
    setMessages(newMessages);
    
    if (!config.apiKeys?.groq) {
      setMessages(prev => [...prev, { role: 'system', content: 'No Groq API key configured. Please type /api to set it up.' }]);
      return;
    }

    await continueAiConversation(newMessages);
  };

  return (
    <Box flexDirection="column" padding={1}>
      <Header />
      
      {mode === 'chat' && (
        <>
          <ResponsePanel messages={messages} />
          <InteractivePrompt onSubmit={handleQuerySubmit} isLoading={isLoading} />
        </>
      )}

      {mode === 'login_select' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Select Login Method:</Text></Box>
          <SelectInput items={[
            { label: 'Firebase Email & Password Auth', value: 'firebase_auth' },
            { label: 'Continue with Google (OAuth)', value: 'google_oauth' }
          ]} onSelect={handleLoginSelect} />
        </Box>
      )}
      
      {mode === 'firebase_email' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Enter your Firebase Email:</Text></Box>
          <Box borderStyle="single" borderColor="cyan" paddingX={1}>
            <TextInput value={emailInput} onChange={setEmailInput} onSubmit={handleEmailSubmit} />
          </Box>
        </Box>
      )}
      
      {mode === 'firebase_password' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Enter your Firebase Password:</Text></Box>
          <Box borderStyle="single" borderColor="cyan" paddingX={1}>
            <TextInput value={passwordInput} onChange={setPasswordInput} onSubmit={handlePasswordSubmit} mask="*" />
          </Box>
        </Box>
      )}

      {mode === 'api_select' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Select AI Provider to configure:</Text></Box>
          <SelectInput items={[
            { label: 'Groq (Fast Open-Source Models)', value: 'groq' },
            { label: 'OpenAI (GPT-4o)', value: 'openai' },
            { label: 'Google Gemini (API Key)', value: 'gemini' },
            { label: 'Anthropic Claude', value: 'anthropic' }
          ]} onSelect={handleApiSelect} />
        </Box>
      )}

      {mode === 'api_input' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Enter your API Key for {selectedProvider}:</Text></Box>
          <Box borderStyle="single" borderColor="cyan" paddingX={1}>
            <TextInput value={apiKeyInput} onChange={setApiKeyInput} onSubmit={handleApiKeySubmit} mask="*" />
          </Box>
        </Box>
      )}

      {mode === 'github_select' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Setup GitHub Authentication:</Text></Box>
          <SelectInput items={[
            { label: 'Generate & Use SSH Key', value: 'ssh' },
            { label: 'Use GitHub CLI (gh)', value: 'gh_cli' }
          ]} onSelect={handleGithubSelect} />
        </Box>
      )}

      {mode === 'config_select' && (
        <Box flexDirection="column" borderStyle="round" borderColor="yellow" padding={1}>
          <Box marginBottom={1}><Text color="yellow" bold>Auto-Approve AI Commands? (No Popups)</Text></Box>
          <SelectInput items={[
            { label: 'Yes - Never ask for permission', value: 'yes' },
            { label: 'No - Always ask for permission', value: 'no' }
          ]} onSelect={handleConfigSelect} />
        </Box>
      )}

      {mode === 'confirm_exec' && pendingCommand && (
        <Box flexDirection="column" borderStyle="round" borderColor="red" padding={1}>
          <Box marginBottom={1}>
            <Text color="red" bold>Luna wants to run a command:</Text>
          </Box>
          <Text color="white">Command: <Text bold color="cyan">{pendingCommand.cmd}</Text></Text>
          <Text color="gray">Reason: {pendingCommand.reason}</Text>
          <Box marginTop={1}>
            <SelectInput items={[
              { label: 'Approve & Run', value: 'yes' },
              { label: 'Deny', value: 'no' }
            ]} onSelect={handleCommandApproval} />
          </Box>
        </Box>
      )}

      <Box marginTop={1} justifyContent="center">
        <Text color="dim">Press Ctrl+C or /exit to exit | Press ESC to return to chat</Text>
      </Box>
    </Box>
  );
};

render(<App />);
