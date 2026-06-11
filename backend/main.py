from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
import re

from backend.config import settings, BASE_DIR
from backend.database import engine, Base
from backend.routers import alerts, screenshots, rules
from backend.services.monitor_service import (
    start_monitor,
    stop_monitor,
    get_monitor_status,
    add_websocket_client,
    remove_websocket_client,
)

from backend.schemas.schemas import MonitorControl, MonitorSettings

# ── Create database tables on startup ──────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Activity Monitor API...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    start_monitor()
    yield
    print("Shutting down...")
    stop_monitor()


# ── Create FastAPI app ──────────────────────────────────
app = FastAPI(
    title="Activity Monitor API",
    description="AI-powered computer activity monitoring system",
    version="1.0.0",
    lifespan=lifespan
)

# ── CORS (allows React frontend to call this API) ───────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://screen-monitoring-ai-system.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve screenshot images as static files ─────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Include all routers ─────────────────────────────────
app.include_router(alerts.router)
app.include_router(screenshots.router)
app.include_router(rules.router)


# ── Monitor control endpoints ───────────────────────────
@app.post("/api/monitor/control")
def control_monitor(body: MonitorControl):
    """Start or stop the monitoring service."""
    if body.action == "start":
        success, message = start_monitor()
    elif body.action == "stop":
        success, message = stop_monitor()
    else:
        return {"success": False, "message": "Invalid action. Use 'start' or 'stop'"}
    
    return {"success": success, "message": message, "status": get_monitor_status()}


@app.get("/api/monitor/status")
def monitor_status():
    """Get current monitor status."""
    return get_monitor_status()


def update_env_file(key: str, value: str):
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    pattern = re.compile(rf"^{key}=.*$", re.MULTILINE)
    if pattern.search(content):
        content = pattern.sub(f"{key}={value}", content)
    else:
        content += f"\n{key}={value}\n"
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

@app.get("/api/monitor/settings", response_model=MonitorSettings)
def get_monitor_settings():
    return MonitorSettings(screenshot_interval_seconds=settings.SCREENSHOT_INTERVAL_SECONDS)

@app.post("/api/monitor/settings")
def update_monitor_settings(body: MonitorSettings):
    settings.SCREENSHOT_INTERVAL_SECONDS = body.screenshot_interval_seconds
    update_env_file("SCREENSHOT_INTERVAL_SECONDS", str(body.screenshot_interval_seconds))
    return {"success": True, "message": "Settings updated"}


# ── WebSocket for real-time frontend updates ────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    add_websocket_client(websocket)
    try:
        while True:
            # Keep connection alive, listen for pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        remove_websocket_client(websocket)


# ── Health check ────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Activity Monitor API is running",
        "docs": "/docs",
        "status": get_monitor_status()
    }
