import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api.routes import router
from backend.api.ws import router as ws_router
from backend.core.context_engine import context_engine

load_dotenv()

app = FastAPI(title="LUNA OS X - AI Core")

from backend.core.voice_agent import voice_agent

@app.on_event("startup")
async def startup_event():
    context_engine.start()
    # Try to start voice agent natively for mic fallback
    try:
        voice_agent.start_background_listening()
    except Exception as e:
        print(f"Failed to start native mic: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    context_engine.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(ws_router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=3000, reload=True)
