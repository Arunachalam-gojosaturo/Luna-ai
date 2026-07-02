import json
from typing import AsyncIterator, Optional
from rich.console import Console

from luna.providers.base import BaseProvider, Message, ToolCall
from luna.chat.chat import ChatSystem
from luna.chat.tools import AVAILABLE_TOOLS, LUNA_TOOLS_SCHEMA
from luna.ui.theme import print_status

console = Console()

class LunaAgent:
    """Agentic loop that can execute tools."""
    
    def __init__(self, chat_system: ChatSystem):
        self.chat_system = chat_system
    
    async def chat(self, user_message: str, **kwargs):
        """Send message and handle tool calls recursively."""
        if not self.chat_system.messages or not any(m.role == "system" for m in self.chat_system.messages):
            system_prompt = (
                "You are LUNA, a powerful AI assistant running in a terminal loop. "
                "You have access to tools to read/write files and execute bash commands. "
                "Use these tools to help the user, explore their codebase, and run tasks autonomously. "
                "Do not ask for permission to run read commands. Provide concise and helpful answers."
            )
            self.chat_system.messages.insert(0, Message(role="system", content=system_prompt))
            
        self.chat_system.add_message("user", user_message)
        
        while True:
            # We don't stream if we expect tool calls, or we stream and buffer.
            # For simplicity, we just use the non-streaming chat when tools are enabled.
            kwargs["tools"] = LUNA_TOOLS_SCHEMA
            try:
                response = await self.chat_system.provider.chat(
                    self.chat_system.messages, 
                    **kwargs
                )
            except Exception as e:
                print_status(f"Provider Error: {e}", "error")
                break
                
            if response.content:
                console.print(f"[magenta]LUNA:[/] {response.content}\n")
                self.chat_system.add_message("assistant", response.content)
            
            if response.tool_calls:
                # Add the assistant's message with tool calls
                msg = Message(role="assistant", content=response.content, tool_calls=response.tool_calls)
                self.chat_system.messages.append(msg)
                
                # Execute tools
                for tc in response.tool_calls:
                    console.print(f"[dim cyan]Executing tool:[/] {tc.name} ({tc.arguments})")
                    try:
                        args = json.loads(tc.arguments)
                        if tc.name in AVAILABLE_TOOLS:
                            result = AVAILABLE_TOOLS[tc.name](**args)
                        else:
                            result = f"Error: Tool {tc.name} not found."
                    except Exception as e:
                        result = f"Error executing tool: {e}"
                    
                    console.print(f"[dim]Result:[/] {result[:200]}...")
                    
                    # Add tool response
                    tool_msg = Message(
                        role="tool", 
                        content=str(result), 
                        tool_call_id=tc.id,
                        name=tc.name
                    )
                    self.chat_system.messages.append(tool_msg)
                
                # Continue loop to send tool results back to the provider
                continue
                
            # No more tool calls, break the loop
            break
            
        if self.chat_system.current_session:
            self.chat_system.history.save_session(self.chat_system.current_session)
