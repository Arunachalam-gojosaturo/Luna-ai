"""
Chat command for LUNA CLI.
Interactive AI chat with streaming and history.
"""

import typer
from rich.console import Console
from rich.prompt import Prompt
import asyncio
from typing import Optional
import uuid

from luna.config import get_config
from luna.core.session import get_session_manager
from luna.chat import ChatSystem
from luna.providers import ProviderRegistry, Message
from luna.ui.theme import print_header, print_status, print_section

console = Console()

chat_app = typer.Typer(help="AI chat with LUNA")


def get_provider_instance():
    """Get current AI provider instance."""
    config = get_config()
    session_mgr = get_session_manager()
    
    provider_name = session_mgr.get_provider() or config.config.default_provider
    provider_cfg = config.get_provider(provider_name)
    
    if not provider_cfg or not provider_cfg.api_key:
        print_status(f"Provider '{provider_name}' not configured", "error")
        print_status("Run 'luna /api add' to configure", "info")
        raise typer.Exit(1)
    
    try:
        provider_class = ProviderRegistry.get(provider_name)
        if not provider_class:
            raise Exception(f"Unknown provider: {provider_name}")
        
        return provider_class(provider_cfg.api_key, model=provider_cfg.model)
    except Exception as e:
        print_status(f"Error: {str(e)}", "error")
        raise typer.Exit(1)


def _start_chat(message: Optional[str] = None, provider: Optional[str] = None, model: Optional[str] = None, session_id: Optional[str] = None):
    """Internal helper to start chat session."""
    # Resolve OptionInfo/ArgumentInfo if passed mistakenly
    if isinstance(message, (typer.models.OptionInfo, typer.models.ArgumentInfo)): message = message.default
    if isinstance(provider, (typer.models.OptionInfo, typer.models.ArgumentInfo)): provider = provider.default
    if isinstance(model, (typer.models.OptionInfo, typer.models.ArgumentInfo)): model = model.default
    if isinstance(session_id, (typer.models.OptionInfo, typer.models.ArgumentInfo)): session_id = session_id.default

    print_header("LUNA Chat", "AI Coding Assistant")
    
    # Set provider if specified
    if provider:
        get_session_manager().set_provider(provider)
    
    # Get provider
    try:
        ai_provider = get_provider_instance()
    except typer.Exit:
        return
    
    # Initialize chat system
    chat_sys = ChatSystem(ai_provider)
    session_mgr = get_session_manager()
    
    # Load or create session
    if session_id:
        if chat_sys.load_session(session_id):
            print_status(f"Loaded session: {session_id}", "success")
        else:
            print_status(f"Session not found: {session_id}", "warning")
            session_id = str(uuid.uuid4())[:8]
    else:
        session_id = str(uuid.uuid4())[:8]
    
    chat_sys.new_session(session_id, provider or session_mgr.get_provider(), model or "")
    session_mgr.set_session(session_id)
    
    console.print(f"[dim]Session: {session_id}[/]")
    console.print("[dim]Type 'exit' to quit, 'clear' to clear chat, 'export' to save[/]\n")
    
    # If initial message provided, send it
    if message:
        console.print(f"[cyan]You:[/] {message}\n")
        asyncio.run(_send_message(chat_sys, message))
    
    # Interactive loop
    while True:
        try:
            user_input = Prompt.ask("[cyan]You[/]", multiline=True)
            
            if not user_input.strip():
                continue
            
            if user_input.lower() == "exit":
                console.print("[yellow]Goodbye![/]")
                break
            
            if user_input.lower() == "clear":
                chat_sys.clear_session()
                console.clear()
                print_header("LUNA Chat", "Chat cleared")
                continue
            
            if user_input.lower() == "export":
                exported = chat_sys.export_session()
                if exported:
                    export_file = f"luna_chat_{session_id}.md"
                    with open(export_file, 'w') as f:
                        f.write(exported)
                    print_status(f"Exported to {export_file}", "success")
                continue
            
            asyncio.run(_send_message(chat_sys, user_input))
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Chat interrupted[/]")
            break
        except Exception as e:
            print_status(f"Error: {str(e)}", "error")

@chat_app.command()
def start(
    message: Optional[str] = typer.Argument(None, help="Initial message"),
    provider: Optional[str] = typer.Option(None, "-p", "--provider", help="AI provider"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="AI model"),
    session_id: Optional[str] = typer.Option(None, "-s", "--session", help="Load session ID"),
):
    """Start interactive chat session."""
    _start_chat(message, provider, model, session_id)


from luna.chat.agent import LunaAgent

async def _send_message(chat_sys: ChatSystem, message: str):
    """Send message and handle response."""
    console.print()
    try:
        agent = LunaAgent(chat_sys)
        with console.status("[cyan]LUNA is thinking...[/]", spinner="dots"):
            await agent.chat(message)
    except Exception as e:
        print_status(f"Error: {str(e)}", "error")


@chat_app.command(name="new")
def new_chat():
    """Start new chat session."""
    _start_chat()


@chat_app.command(name="history")
def show_history(limit: int = typer.Option(10, "-n", "--number", help="Number of sessions")):
    """Show chat history."""
    print_header("Chat History")
    
    from luna.chat import ChatHistory
    history = ChatHistory()
    sessions = history.list_sessions(limit)
    
    if not sessions:
        console.print("[yellow]No chat sessions[/]")
        return
    
    console.print(f"[cyan]Recent sessions:[/]")
    for i, session_id in enumerate(sessions, 1):
        session = history.load_session(session_id)
        if session:
            msg_count = len(session.messages)
            console.print(f"  {i}. {session.id} ({msg_count} messages) — {session.provider}")


@chat_app.command(name="continue")
def continue_session(
    session_id: str = typer.Argument(help="Session ID to continue"),
):
    """Continue previous chat session."""
    _start_chat(session_id=session_id)


@chat_app.command(name="export")
def export_chat(session_id: str = typer.Argument(help="Session ID to export")):
    """Export chat session to markdown."""
    from luna.chat import ChatHistory
    history = ChatHistory()
    session = history.load_session(session_id)
    
    if not session:
        print_status(f"Session not found: {session_id}", "error")
        return
    
    chat_sys = ChatSystem(None)
    chat_sys.current_session = session
    
    exported = chat_sys.export_session()
    if exported:
        export_file = f"luna_chat_{session_id}.md"
        with open(export_file, 'w') as f:
            f.write(exported)
        print_status(f"Exported to {export_file}", "success")


def main():
    """Main chat entry point."""
    chat_app()


if __name__ == "__main__":
    chat_app()
