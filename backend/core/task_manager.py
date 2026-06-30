import asyncio
from typing import Dict, Any, Callable

class ConnectionManager:
    def __init__(self):
        self.active_connections: list = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: dict):
        message = {"type": event_type, "payload": payload}
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"WS send error: {e}")

ws_manager = ConnectionManager()

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        # Simple event queue for internal components to wait on confirmation
        self.pending_confirmations: Dict[str, asyncio.Event] = {}
        self.confirmation_results: Dict[str, bool] = {}

    async def start_task(self, task_id: str, name: str, coro):
        self.tasks[task_id] = {
            "id": task_id,
            "name": name,
            "status": "running",
            "progress": "Starting...",
            "logs": []
        }
        await self._broadcast_task_update(task_id)
        
        task = asyncio.create_task(self._run_task(task_id, coro))
        return task

    async def _run_task(self, task_id: str, coro):
        try:
            result = await coro
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = "Completed."
            self.tasks[task_id]["result"] = result
        except Exception as e:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["progress"] = f"Failed: {str(e)}"
        
        await self._broadcast_task_update(task_id)

    async def update_progress(self, task_id: str, progress: str):
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            self.tasks[task_id]["logs"].append(progress)
            await self._broadcast_task_update(task_id)

    async def _broadcast_task_update(self, task_id: str):
        await ws_manager.broadcast("task_update", self.tasks[task_id])

    async def request_confirmation(self, task_id: str, prompt: str) -> bool:
        """
        Pauses the task and asks the user for confirmation over WebSockets.
        """
        event = asyncio.Event()
        self.pending_confirmations[task_id] = event
        
        # Broadcast confirmation request
        await ws_manager.broadcast("confirmation_required", {
            "task_id": task_id,
            "prompt": prompt
        })
        
        # Wait until resume_task is called
        await event.wait()
        
        result = self.confirmation_results.pop(task_id, False)
        del self.pending_confirmations[task_id]
        return result

    async def provide_confirmation(self, task_id: str, confirmed: bool):
        if task_id in self.pending_confirmations:
            self.confirmation_results[task_id] = confirmed
            self.pending_confirmations[task_id].set()

task_manager = TaskManager()
