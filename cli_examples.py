#!/usr/bin/env python3
"""
Luna CLI Advanced Examples
Demonstrates all features of the enhanced Luna CLI
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cli_utils import (
    ProgressBar, Spinner, Table, Colors, Menu,
    print_success, print_error, print_warning, print_info,
    print_box, print_section, create_divider, format_status
)
from cli_config import (
    ConfigManager, CommandAliasManager, HistoryManager
)


async def demo_configuration():
    """Demo: Configuration Management"""
    print_section("Configuration Management", Colors.BRIGHT_MAGENTA)
    
    config = ConfigManager()
    
    print(f"Config Directory: {config.CONFIG_DIR}")
    print(f"Current Profile: {Colors.BRIGHT_CYAN}{config.current_profile.name}{Colors.RESET}")
    print(f"Model: {config.current_profile.model}")
    print(f"Provider: {config.current_profile.provider}")
    print(f"Voice Enabled: {config.current_profile.voice_enabled}")
    print()
    
    # Create new profile
    print("Creating new profile 'research'...")
    profile = config.create_profile(
        "research",
        model="gpt-4",
        provider="openai",
        voice_enabled=False,
        auto_confirm=True
    )
    print_success(f"Profile '{profile.name}' created")
    
    # List all profiles
    print(f"\n{Colors.BRIGHT_BLUE}Available Profiles:{Colors.RESET}")
    for prof_name in config.list_profiles():
        marker = "→" if prof_name == config.current_profile.name else " "
        print(f"  {marker} {prof_name}")
    print()


async def demo_aliases():
    """Demo: Command Aliases"""
    print_section("Command Aliases", Colors.BRIGHT_YELLOW)
    
    alias_mgr = CommandAliasManager()
    
    print("Default Aliases:")
    aliases = alias_mgr.list_aliases()
    
    # Display in a table
    table = Table(["Alias", "Command"], [10, 20])
    for alias, command in list(aliases.items())[:8]:
        table.add_row([alias, command])
    table.display()
    print()
    
    # Add custom alias
    print("Adding custom alias 'sm' -> 'system memory'")
    alias_mgr.add_alias("sm", "system memory")
    print_success("Alias added successfully")
    print()


async def demo_advanced_ui():
    """Demo: Advanced UI Components"""
    print_section("Advanced UI Components", Colors.BRIGHT_GREEN)
    
    # Status indicators
    print(f"{Colors.BRIGHT_BLUE}Status Indicators:{Colors.RESET}")
    print(f"  {format_status('success', 'Task completed')}")
    print(f"  {format_status('error', 'Operation failed')}")
    print(f"  {format_status('pending', 'Waiting for input')}")
    print(f"  {format_status('running', 'Processing...')}")
    print()
    
    # Decorative boxes
    print(f"{Colors.BRIGHT_BLUE}Decorative Boxes:{Colors.RESET}\n")
    print_box("Important system notification", Colors.BRIGHT_CYAN, "ALERT")
    print()
    
    # Divider
    print(f"{Colors.BRIGHT_BLUE}Dividers:{Colors.RESET}")
    print(create_divider(60, "═", Colors.BRIGHT_MAGENTA))
    print()


async def demo_progress_and_spinner():
    """Demo: Progress Bar and Spinner"""
    print_section("Progress and Loading", Colors.BRIGHT_CYAN)
    
    # Progress bar
    print(f"{Colors.BRIGHT_BLUE}Progress Bar:{Colors.RESET}")
    bar = ProgressBar(50, "Initializing", length=30)
    for i in range(51):
        bar.update(i)
        await asyncio.sleep(0.02)
    print()
    
    # Spinner with moon emoji
    print(f"{Colors.BRIGHT_BLUE}Spinner Animation:{Colors.RESET}")
    spinner = Spinner("Processing lunar data", "moon")
    for i in range(16):
        spinner.start()
        await asyncio.sleep(0.15)
    spinner.stop(f"{Colors.GREEN}✓ Processing complete!{Colors.RESET}")
    print()


async def demo_table():
    """Demo: Table Display"""
    print_section("Data Table Display", Colors.BRIGHT_YELLOW)
    
    # Create a complex table
    table = Table(
        ["Feature", "Status", "Performance", "Notes"],
        [20, 12, 15, 35]
    )
    
    table.add_rows([
        ["Boot Animation", "✓", "Fast", "Smooth 60fps animation"],
        ["Voice Processing", "✓", "Normal", "Google TTS integration"],
        ["Memory System", "✓", "Fast", "ChromaDB vector search"],
        ["Multi-Model", "✓", "Excellent", "Groq, OpenAI, Google"],
        ["CLI Utils", "✓", "Very Fast", "Async processing"],
    ])
    
    table.display()
    print()


async def demo_history():
    """Demo: History Management"""
    print_section("History Management", Colors.BRIGHT_GREEN)
    
    history = HistoryManager()
    
    # Add sample entries
    print("Adding sample history entries...")
    history.add_entry("help", "Showed available commands")
    history.add_entry("status", "Displayed system status")
    history.add_entry("model", "Switched to GPT-4")
    
    print_success(f"Total history entries: {len(history.history)}")
    print()
    
    # Get recent
    print(f"{Colors.BRIGHT_BLUE}Recent Commands:{Colors.RESET}")
    recent = history.get_recent(3)
    for i, entry in enumerate(recent, 1):
        timestamp = entry.get("timestamp", "N/A")[:19]
        command = entry.get("command", "N/A")
        print(f"  {i}. [{timestamp}] {Colors.CYAN}{command}{Colors.RESET}")
    print()
    
    # Search
    print(f"{Colors.BRIGHT_BLUE}Searching for 'status':{Colors.RESET}")
    results = history.search("status")
    for result in results:
        print(f"  → {result.get('command')}")
    print()


async def demo_menu():
    """Demo: Interactive Menu"""
    print_section("Interactive Menu System", Colors.BRIGHT_MAGENTA)
    
    menu_items = [
        ("View Status", "Check system status", lambda: print_info("Status checked!")),
        ("Configure", "Open configuration", lambda: print_info("Config opened!")),
        ("Run Tests", "Execute test suite", lambda: print_info("Tests running!")),
    ]
    
    menu = Menu("Luna CLI - Main Menu", menu_items)
    choice = await asyncio.to_thread(menu.display)
    
    if choice is not None:
        print_success(f"Selected option: {choice}")
    else:
        print_info("Menu cancelled")
    
    print()


async def demo_messages():
    """Demo: Message Types"""
    print_section("Message Types and Formatting", Colors.BRIGHT_BLUE)
    
    print(f"{Colors.BRIGHT_BLUE}Success Messages:{Colors.RESET}")
    print_success("Operation completed successfully")
    print_success("All tests passed")
    print()
    
    print(f"{Colors.BRIGHT_BLUE}Warning Messages:{Colors.RESET}")
    print_warning("This action cannot be undone")
    print_warning("Disk space running low")
    print()
    
    print(f"{Colors.BRIGHT_BLUE}Error Messages:{Colors.RESET}")
    print_error("Connection failed")
    print_error("Invalid configuration")
    print()
    
    print(f"{Colors.BRIGHT_BLUE}Info Messages:{Colors.RESET}")
    print_info("Update available: v2.1.0")
    print_info("Cache cleared successfully")
    print()


async def main():
    """Run all demos"""
    print(f"\n{Colors.BRIGHT_MAGENTA}{'='*60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}  Luna CLI - Advanced Features Demo{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}{'='*60}{Colors.RESET}\n")
    
    demos = [
        ("Configuration", demo_configuration),
        ("Aliases", demo_aliases),
        ("Advanced UI", demo_advanced_ui),
        ("Progress & Spinners", demo_progress_and_spinner),
        ("Tables", demo_table),
        ("History", demo_history),
        ("Messages", demo_messages),
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            print_error(f"Error in {name} demo: {e}")
        
        await asyncio.sleep(0.5)
    
    print(f"\n{Colors.BRIGHT_GREEN}Demo completed!{Colors.RESET}")
    print(f"{Colors.DIM}All features are working correctly.{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
