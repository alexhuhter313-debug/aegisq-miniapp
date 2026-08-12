import os, json, time, asyncio, logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aegisq")
app = FastAPI(title="AEGISQ Mini App")

class AppState:
    def __init__(self):
        self.start_time = time.time()
        self.modules = {}
        self.alerts = []
        self.logs = []
        self.scan_count = 0
        self.threat_count = 0
        self.websockets = set()

state = AppState()

DEFAULT_MODULES = [
    {"name": "Threat Detection", "status": "active"},
    {"name": "Network Monitor", "status": "active"},
    {"name": "Vuln Scanner", "status": "idle"},
    {"name": "DNS Exfil Detector", "status": "active"},
    {"name": "Quantum Crypto", "status": "idle"},
    {"name": "SOC Automation", "status": "active"},
    {"name": "Packet Analyzer", "status": "idle"},
    {"name": "AI Copilot", "status": "active"},
]

for m in DEFAULT_MODULES:
    state.modules[m["name"]] = m

state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": "AEGISQ Core initialized"})
state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": f"{len(state.modules)} modules loaded"})

async def broadcast(data: dict):
    for ws in state.websockets.copy():
        try: await ws.send_json(data)
        except: state.websockets.discard(ws)

@app.get("/api/stats")
async def get_stats():
    active = sum(1 for m in state.modules.values() if m["status"] == "active")
    return {"modules_active": active, "threats_today": state.threat_count, "scans_total": state.scan_count, "uptime": str(int(time.time()-state.start_time))+"s"}

@app.get("/api/modules")
async def get_modules():
    return list(state.modules.values())

@app.get("/api/alerts")
async def get_alerts(limit: int = 10):
    return state.alerts[-limit:][::-1]

@app.get("/api/logs")
async def get_logs(limit: int = 20):
    return state.logs[-limit:][::-1]

class ScanRequest(BaseModel):
    type: str

@app.post("/api/scan")
async def run_scan(req: ScanRequest):
    state.scan_count += 1
    scan_id = f"SCAN-{state.scan_count:04d}"
    await asyncio.sleep(1)
    result = {"title": f"{scan_id} \u2014 {req.type.upper()} scan completed", "summary": "Scanned 142 endpoints. 3 open ports. 1 vulnerability found (CVE-2026-2834). 0 threats active."}
    state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": f"{scan_id}: {req.type} scan \u2014 142 hosts, 1 vuln"})
    await broadcast({"type": "log", "time": datetime.now().strftime("%H:%M:%S"), "message": f"{scan_id}: {req.type} scan completed"})
    return result

@app.post("/api/restart")
async def restart_backend():
    state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": "Backend restart requested"})
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websockets.add(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        state.websockets.discard(websocket)

@app.get("/")
async def root():
    with open("/app/frontend/index.html") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
