#!/usr/bin/env python3
"""
🌙 Luna OS X - Enhanced Command Line Interface
Enhanced CLI with animations, attributes, and rich UI
"""

import asyncio
import json
import httpx
import websockets
import sys
import os
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

# ANSI Color codes
class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    
    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class CommandStatus(Enum):
    """Command status enum"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class CLICommand:
    """Represents a CLI command with metadata"""
    name: str
    description: str
    aliases: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    category: str = "general"
    status: CommandStatus = CommandStatus.PENDING


@dataclass
class CLISession:
    """Represents a CLI session with attributes"""
    session_id: str
    created_at: datetime
    user: str = "default"
    model: str = "groq"
    provider: str = "groq"
    history: List[Dict[str, str]] = field(default_factory=list)
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "session_id": self.session_id,
            "user": self.user,
            "uptime": str(datetime.now() - self.created_at),
            "total_commands": self.total_commands,
            "success_rate": (self.successful_commands / max(self.total_commands, 1)) * 100
        }


class BootAnimation:
    """Awesome boot animation for Luna CLI"""
    
    @staticmethod
    def print_colored(text: str, color: str = Colors.RESET, delay: float = 0.05) -> None:
        """Print colored text with delay"""
        for char in text:
            print(f"{color}{char}{Colors.RESET}", end="", flush=True)
            time.sleep(delay)
        print()
    
    @staticmethod
    def luna_logo() -> None:
        """Print Luna logo"""
        logo = r"""
        ██╗     ██╗   ██╗███╗   ██╗ █████╗ 
        ██║     ██║   ██║████╗  ██║██╔══██╗
        ██║     ██║   ██║██╔██╗ ██║███████║
        ██║     ██║   ██║██║╚██╗██║██╔══██║
        ███████╗╚██████╔╝██║ ╚████║██║  ██║
        ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
        """
        print(f"{Colors.BRIGHT_CYAN}{logo}{Colors.RESET}")
    
    @staticmethod
    def boot_sequence() -> None:
        """Execute full boot sequence with animation"""
        print(f"\n{Colors.BRIGHT_MAGENTA}{'='*60}{Colors.RESET}")
        
        BootAnimation.luna_logo()
        
        print(f"\n{Colors.BRIGHT_BLUE}Initializing Luna OS X CLI...{Colors.RESET}\n")
        
        stages = [
            ("🔄 Loading core modules", 0.8),
            ("🧠 Initializing AI brain", 1.0),
            ("🗣️  Configuring voice engine", 0.6),
            ("💾 Setting up memory system", 0.7),
            ("🔐 Authenticating with backend", 0.9),
            ("⚙️  Configuring CLI environment", 0.5),
            ("✨ Ready for commands", 0.3),
        ]
        
        for stage, duration in stages:
            print(f"{Colors.BRIGHT_GREEN}▸{Colors.RESET} {stage}", end="", flush=True)
            
            # Animated waiting dots
            for _ in range(3):
                time.sleep(duration / 3)
                print(".", end="", flush=True)
            
            print(f" {Colors.GREEN}✓{Colors.RESET}")
        
        print(f"\n{Colors.BRIGHT_MAGENTA}{'='*60}{Colors.RESET}\n")
        print(f"{Colors.BRIGHT_GREEN}Luna OS X CLI v2.0 Ready!{Colors.RESET}")
        print(f"{Colors.DIM}Type 'help' for available commands or 'exit' to quit.{Colors.RESET}\n")


class LunaCliEnhanced:
    """Enhanced Luna CLI with rich features"""
    
    API_URL = "http://localhost:3000/api/luna/command"
    WS_URL = "ws://localhost:3000/api/ws/events"
    HISTORY_URL = "http://localhost:3000/api/history?session_id=default"
    
    def __init__(self):
        """Initialize the enhanced CLI"""
        self.session = CLISession(
            session_id="cli-" + str(int(time.time())),
            created_at=datetime.now()
        )
        
        self.commands: Dict[str, CLICommand] = self._init_commands()
        self.running = False
        self.ws_connection = None
        
    def _init_commands(self) -> Dict[str, CLICommand]:
        """Initialize available commands"""
        return {
            "help": CLICommand(
                name="help",
                description="Show available commands",
                aliases=["h", "?"],
                category="system"
            ),
            "status": CLICommand(
                name="status",
                description="Show Luna system status",
                aliases=["stat"],
                category="system"
            ),
            "history": CLICommand(
                name="history",
                description="Show command history",
                aliases=["hist"],
                category="system"
            ),
            "clear": CLICommand(
                name="clear",
                description="Clear screen",
                aliases=["cls"],
                category="system"
            ),
            "voice": CLICommand(
                name="voice",
                description="Toggle voice output",
                aliases=["v"],
                category="system"
            ),
            "model": CLICommand(
                name="model",
                description="Switch AI model/provider",
                aliases=["m"],
                category="config"
            ),
            "memory": CLICommand(
                name="memory",
                description="Manage Luna's memory",
                aliases=["mem"],
                category="memory"
            ),
            "exit": CLICommand(
                name="exit",
                description="Exit Luna CLI",
                aliases=["quit", "q"],
                category="system"
            ),
        }
    
    def _format_header(self, text: str) -> str:
        """Format section header"""
        return f"\n{Colors.BRIGHT_CYAN}╔{'═' * 58}╗{Colors.RESET}\n{Colors.BRIGHT_CYAN}║ {text:<56} ║{Colors.RESET}\n{Colors.BRIGHT_CYAN}╚{'═' * 58}╝{Colors.RESET}\n"
    
    def _format_command_prompt(self) -> str:
        """Format the command prompt"""
        return f"\n{Colors.BRIGHT_MAGENTA}luna{Colors.RESET}> "
    
    async def handle_help(self) -> None:
        """Handle help command"""
        print(self._format_header("Available Commands"))
        
        categories = {}
        for cmd_name, cmd in self.commands.items():
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append((cmd_name, cmd))
        
        for category, cmds in sorted(categories.items()):
            print(f"\n{Colors.BRIGHT_YELLOW}{category.upper()}{Colors.RESET}")
            for cmd_name, cmd in cmds:
                aliases = f"({', '.join(cmd.aliases)})" if cmd.aliases else ""
                print(f"  {Colors.GREEN}{cmd_name:<15}{Colors.RESET} {cmd.description} {Colors.DIM}{aliases}{Colors.RESET}")
        
        print(f"\n{Colors.DIM}Use 'help <command>' for more details{Colors.RESET}")
    
    async def handle_status(self) -> None:
        """Handle status command"""
        print(self._format_header("Luna System Status"))
        
        stats = self.session.get_stats()
        
        status_items = [
            ("🆔 Session ID", stats["session_id"]),
            ("👤 User", stats["user"]),
            ("⏱️  Uptime", stats["uptime"]),
            ("📊 Total Commands", str(stats["total_commands"])),
            ("✅ Success Rate", f"{stats['success_rate']:.1f}%"),
            ("🤖 Model", self.session.model),
            ("🔌 Provider", self.session.provider),
        ]
        
        for label, value in status_items:
            print(f"{label:<20} {Colors.BRIGHT_BLUE}{value}{Colors.RESET}")
    
    async def handle_history(self) -> None:
        """Handle history command"""
        if not self.session.history:
            print(f"{Colors.YELLOW}No history available{Colors.RESET}")
            return
        
        print(self._format_header("Command History"))
        
        for i, msg in enumerate(self.session.history[-10:], 1):
            role = "You" if msg['role'] == "user" else "🤖"
            print(f"{Colors.DIM}{i:2d}.{Colors.RESET} {role:<4} {msg['content']}")
    
    async def handle_clear(self) -> None:
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    async def handle_memory(self) -> None:
        """Handle memory management"""
        print(self._format_header("Memory Management"))
        
        submenu_items = [
            ("list", "List all memories"),
            ("search", "Search memories"),
            ("clear", "Clear all memories"),
            ("stats", "Memory statistics"),
        ]
        
        for cmd, desc in submenu_items:
            print(f"  {Colors.GREEN}{cmd:<15}{Colors.RESET} {desc}")
    
    async def handle_model(self) -> None:
        """Handle model switching"""
        print(self._format_header("AI Model Selection"))
        
        providers = [
            ("1", "Groq (Fast, Free)", "groq"),
            ("2", "OpenAI (Advanced)", "openai"),
            ("3", "Google GenAI", "google"),
            ("4", "OpenRouter", "openrouter"),
        ]
        
        for num, name, key in providers:
            print(f"  {Colors.BRIGHT_YELLOW}{num}{Colors.RESET}. {name}")
    
    async def process_local_command(self, cmd: str) -> bool:
        """Process local CLI commands, return True if handled locally"""
        cmd_lower = cmd.strip().lower().split()[0]
        
        # Check command and aliases
        for cmd_name, cmd_obj in self.commands.items():
            if cmd_lower == cmd_name or cmd_lower in cmd_obj.aliases:
                if cmd_name == "help":
                    await self.handle_help()
                elif cmd_name == "status":
                    await self.handle_status()
                elif cmd_name == "history":
                    await self.handle_history()
                elif cmd_name == "clear":
                    await self.handle_clear()
                elif cmd_name == "memory":
                    await self.handle_memory()
                elif cmd_name == "model":
                    await self.handle_model()
                elif cmd_name == "exit":
                    return False
                return True
        
        return False
    
    async def listen_ws(self) -> None:
        """Listen for WebSocket events"""
        try:
            async with websockets.connect(self.WS_URL) as ws:
                self.ws_connection = ws
                while self.running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)
                        
                        if data.get("type") == "task_update":
                            task = data.get("payload", {})
                            status_indicator = {
                                "running": "⏳",
                                "completed": "✓",
                                "failed": "✗"
                            }.get(task.get("status"), "•")
                            
                            print(f"\r\033[K{Colors.BRIGHT_BLUE}[{status_indicator} Task: {task.get('name')}]{Colors.RESET} {task.get('progress')}", end="", flush=True)
                            
                            if task.get("status") in ["completed", "failed"]:
                                print(f"\n{Colors.GREEN}[Task Complete] {task.get('name')}{Colors.RESET}")
                            
                            print(self._format_command_prompt(), end="", flush=True)
                        
                        elif data.get("type") == "confirmation_required":
                            task_id = data.get("payload", {}).get("task_id")
                            prompt = data.get("payload", {}).get("prompt")
                            print(f"\n\n{Colors.BRIGHT_YELLOW}[CONFIRMATION REQUIRED]{Colors.RESET} {prompt} (y/n)")
                            ans = await asyncio.to_thread(input, "Your answer: ")
                            confirmed = ans.lower().startswith("y")
                            await ws.send(json.dumps({
                                "type": "provide_confirmation",
                                "payload": {"task_id": task_id, "confirmed": confirmed}
                            }))
                            print(self._format_command_prompt(), end="", flush=True)
                    
                    except asyncio.TimeoutError:
                        continue
                    
        except Exception as e:
            if self.running:
                print(f"\n{Colors.RED}[Error] WebSocket connection lost: {e}{Colors.RESET}")
    
    async def send_command(self, cmd: str) -> Optional[str]:
        """Send command to Luna backend"""
        payload = {
            "command": cmd,
            "activeView": "cli",
            "deviceStates": [],
            "history": self.session.history,
            "groqKey": os.getenv("GROQ_API_KEY", ""),
            "openRouterKey": os.getenv("OPENROUTER_API_KEY", ""),
            "openaiKey": os.getenv("OPENAI_API_KEY", ""),
            "modelSelection": self.session.model,
            "activeProvider": self.session.provider
        }
        
        try:
            print(f"\n{Colors.BRIGHT_BLUE}⏳ Processing...{Colors.RESET}", end="", flush=True)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(self.API_URL, json=payload)
                res.raise_for_status()
                data = res.json()
                
                response = data.get('speech', 'Command executed')
                
                print(f"\r\033[K", end="")
                print(f"\n{Colors.BRIGHT_GREEN}[🤖 Luna]{Colors.RESET} {response}")
                
                # Add to history
                self.session.history.append({"role": "user", "content": cmd})
                self.session.history.append({"role": "assistant", "content": response})
                self.session.total_commands += 1
                self.session.successful_commands += 1
                
                return response
        
        except Exception as e:
            self.session.failed_commands += 1
            print(f"\r\033[K", end="")
            print(f"\n{Colors.RED}[Error] {e}{Colors.RESET}")
            return None
    
    async def load_history(self) -> None:
        """Load recent command history from backend"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(self.HISTORY_URL)
                if res.status_code == 200:
                    history = res.json()
                    self.session.history = history[-20:]  # Keep last 20
                    
                    print(f"{Colors.DIM}Loaded {len(self.session.history)} recent commands{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.DIM}Could not load history: {e}{Colors.RESET}")
    
    async def main(self) -> None:
        """Main CLI loop"""
        # Show boot animation
        BootAnimation.boot_sequence()
        
        # Load history
        await self.load_history()
        
        self.running = True
        
        # Start WebSocket listener in background
        ws_task = asyncio.create_task(self.listen_ws())
        
        try:
            while self.running:
                try:
                    cmd = await asyncio.to_thread(input, self._format_command_prompt().strip() + " > ")
                    
                    if not cmd.strip():
                        continue
                    
                    # Try to handle as local command
                    if await self.process_local_command(cmd):
                        if cmd.strip().lower() in ["exit", "quit", "q"]:
                            self.running = False
                            break
                        continue
                    
                    # Send to Luna backend
                    if cmd.strip():
                        await self.send_command(cmd)
                
                except (KeyboardInterrupt, EOFError):
                    print(f"\n{Colors.YELLOW}Exiting Luna CLI...{Colors.RESET}")
                    self.running = False
                    break
        
        finally:
            self.running = False
            ws_task.cancel()
            
            # Print final stats
            print(f"\n{self._format_header('Session Summary')}")
            stats = self.session.get_stats()
            for key, value in stats.items():
                print(f"{Colors.CYAN}{key:<20}{Colors.RESET} {value}")
            
            print(f"\n{Colors.BRIGHT_MAGENTA}Thank you for using Luna OS X!{Colors.RESET}\n")


async def main():
    """Entry point"""
    cli = LunaCliEnhanced()
    await cli.main()


if __name__ == "__main__":
    if os.name == 'nt':
        os.system('')  # Enable VT100 ANSI sequences on Windows CMD / PowerShell
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
