import asyncio
import json
import httpx
import websockets
import sys
import os

API_URL = "http://localhost:3000/api/luna/command"
WS_URL = "ws://localhost:3000/api/ws/events"
HISTORY_URL = "http://localhost:3000/api/history?session_id=default"

async def listen_ws():
    try:
        async with websockets.connect(WS_URL) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if data.get("type") == "task_update":
                    task = data.get("payload", {})
                    print(f"\r\033[K[Task: {task.get('name')}] {task.get('progress')}")
                    if task.get("status") in ["completed", "failed"]:
                        print(f"[Task: {task.get('name')}] Finished with status: {task.get('status')}")
                    print("LUNA> ", end="", flush=True)

                elif data.get("type") == "confirmation_required":
                    task_id = data.get("payload", {}).get("task_id")
                    prompt = data.get("payload", {}).get("prompt")
                    print(f"\n\n[CONFIRMATION REQUIRED] {prompt} (y/n)")
                    ans = await asyncio.to_thread(input, "Your answer: ")
                    confirmed = ans.lower().startswith("y")
                    await ws.send(json.dumps({
                        "type": "provide_confirmation",
                        "payload": {"task_id": task_id, "confirmed": confirmed}
                    }))
                    print("LUNA> ", end="", flush=True)
                    
    except Exception as e:
        print(f"\nWS connection lost: {e}")

async def send_command(cmd: str):
    # Try to read keys from local UI storage if possible, else rely on env vars or backend defaults.
    # We will just pass empty keys, assuming the backend can fallback to OS env vars.
    payload = {
        "command": cmd,
        "activeView": "cli",
        "deviceStates": [],
        "history": [], # Handled by backend now
        "groqKey": os.getenv("GROQ_API_KEY", ""),
        "openRouterKey": os.getenv("OPENROUTER_API_KEY", ""),
        "openaiKey": os.getenv("OPENAI_API_KEY", ""),
        "modelSelection": "",
        "activeProvider": "groq"
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(API_URL, json=payload)
            res.raise_for_status()
            data = res.json()
            print(f"\n[LUNA] {data.get('speech')}")
    except Exception as e:
        print(f"\n[Error] {e}")

async def main():
    print("========================================")
    print(" LUNA OS X - Command Line Interface     ")
    print("========================================")
    
    # Load recent history
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(HISTORY_URL)
            if res.status_code == 200:
                history = res.json()
                for msg in history[-5:]: # Show last 5
                    role = "You" if msg['role'] == "user" else "LUNA"
                    print(f"[{role}] {msg['content']}")
    except Exception:
        print("Could not load history.")
        
    print("\nType your command below. Type 'exit' to quit.\n")
    
    # Run WS listener in background
    asyncio.create_task(listen_ws())
    
    while True:
        try:
            cmd = await asyncio.to_thread(input, "LUNA> ")
            if cmd.strip().lower() in ["exit", "quit"]:
                break
            if cmd.strip():
                await send_command(cmd)
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
