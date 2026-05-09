import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from simulator.manager import PlcManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PLC Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for frontend
import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

manager = PlcManager()

# --- Models ---
class DisconnectEvent(BaseModel):
    interval_sec: int
    chance_percent: int

class PlcConfig(BaseModel):
    name: str
    series: str = "Q"
    port: int = 5000
    disconnect_event: Optional[DisconnectEvent] = None
    script_interval_ms: int = 1000

class ScriptData(BaseModel):
    code: str

class WriteData(BaseModel):
    address: int
    values: List[int]

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

def plc_update_callback(plc_name: str, start_addr: int, length: int, values: Optional[List[int]]):
    # If script triggered update, values might be None, and we just signal frontend to poll or we could send specific changes.
    # For simplicity, just send a notification event. Frontend can request full data if needed.
    msg = {
        "event": "update",
        "plc": plc_name,
        "address": start_addr,
        "length": length,
        "values": values
    }
    # Need to run in event loop
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(ws_manager.broadcast(json.dumps(msg)))

manager.set_update_callback(plc_update_callback)

@app.on_event("startup")
async def startup_event():
    # Start PLCs that were running (or maybe start none by default?)
    # Let's not auto-start unless configured. For now, manual start.
    pass

@app.on_event("shutdown")
async def shutdown_event():
    await manager.stop_all()

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# --- REST API ---

@app.get("/api/plcs")
def get_plcs():
    res = []
    for name, plc in manager.plcs.items():
        res.append({
            "name": plc.name,
            "port": plc.port,
            "series": plc.series,
            "is_running": plc.is_running,
            "script_interval_ms": plc.script_interval_ms,
            "disconnect_event": {
                "interval_sec": plc.disc_interval,
                "chance_percent": plc.disc_chance
            }
        })
    return res

@app.post("/api/plcs")
def create_plc(config: PlcConfig):
    cfg_dict = config.dict(exclude_none=True)
    manager.create_plc(cfg_dict)
    return {"status": "ok"}

@app.put("/api/plcs/{name}")
def update_plc(name: str, config: PlcConfig):
    cfg_dict = config.dict(exclude_none=True)
    manager.update_plc(name, cfg_dict)
    return {"status": "ok"}

@app.delete("/api/plcs/{name}")
def delete_plc(name: str):
    manager.delete_plc(name)
    return {"status": "ok"}

@app.post("/api/plcs/{name}/start")
async def start_plc(name: str):
    plc = manager.get_plc(name)
    if plc:
        await plc.start()
        return {"status": "ok", "is_running": plc.is_running}
    return {"error": "Not found"}

@app.post("/api/plcs/{name}/stop")
async def stop_plc(name: str):
    plc = manager.get_plc(name)
    if plc:
        await plc.stop()
        return {"status": "ok", "is_running": plc.is_running}
    return {"error": "Not found"}

@app.get("/api/plcs/{name}/script")
def get_script(name: str):
    code = manager.get_script(name)
    return {"code": code}

@app.post("/api/plcs/{name}/script")
def save_script(name: str, data: ScriptData):
    manager.save_script(name, data.code)
    return {"status": "ok"}

@app.get("/api/plcs/{name}/memory")
def get_memory(name: str, start: int = 0, length: int = 100):
    plc = manager.get_plc(name)
    if not plc:
        return {"error": "Not found"}
    try:
        values = plc.read_d_registers(start, length)
        return {"start": start, "length": length, "values": values}
    except ValueError as e:
        return {"error": str(e)}

@app.post("/api/plcs/{name}/memory")
def write_memory(name: str, data: WriteData):
    plc = manager.get_plc(name)
    if not plc:
        return {"error": "Not found"}
    try:
        plc.write_d_registers(data.address, data.values)
        return {"status": "ok"}
    except ValueError as e:
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages if necessary
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
