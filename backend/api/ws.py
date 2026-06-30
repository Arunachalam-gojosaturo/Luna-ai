from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from backend.core.task_manager import ws_manager, task_manager

router = APIRouter()

@router.websocket("/api/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages from clients, such as confirmations
            if data.get("type") == "provide_confirmation":
                task_id = data.get("payload", {}).get("task_id")
                confirmed = data.get("payload", {}).get("confirmed", False)
                if task_id:
                    await task_manager.provide_confirmation(task_id, confirmed)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
