"""AEGISQ Mini App Backend — powered by real shadow313 modules."""
import os, json, time, asyncio, logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aegisq")
app = FastAPI(title="AEGISQ Mini App")

# ── Real shadow313 engine ──
try:
    from shadow313.core.kernel import Kernel
    from shadow313.tools.nexusprobe import NexusProbe
    from shadow313.modules.fortress.defense import FortressEngine
    from shadow313.modules.fortress.offense import OffenseEngine
    REAL_MODULES = True
    logger.info("shadow313 modules loaded \u2014 real detection engine active")
except ImportError:
    logger.warning("shadow313 not installed \u2014 using mock modules")
    REAL_MODULES = False


class AppState:
    def __init__(self):
        self.start_time = time.time()
        self.modules = {}
        self.alerts = []
        self.logs = []
        self.scan_count = 0
        self.threat_count = 0
        self.websockets = set()
        self._init_engine()

    def _init_engine(self):
        if REAL_MODULES:
            self.kernel = Kernel(verbose=True)
            self.nexus = NexusProbe()
            self.fortress = FortressEngine()
            self.offense = OffenseEngine()
            self.modules = {
                "Kernel": {"name": "Kernel", "status": "active", "desc": "Central orchestrator"},
                "NexusProbe": {"name": "NexusProbe", "status": "active", "desc": "AI attack surface mapper"},
                "Fortress": {"name": "Fortress Defense", "status": "active", "desc": "Defensive mesh"},
                "Vuln Scanner": {"name": "Vuln Scanner", "status": "idle", "desc": "CVE & misconfig scan"},
                "AI Copilot": {"name": "AI Copilot", "status": "active", "desc": "LLM-assisted analysis"},
            }
        else:
            self.kernel = None
            self.nexus = None
            self.fortress = None
            self.offense = None
            self.modules = {
                "Threat Detection": {"name": "Threat Detection", "status": "active", "desc": ""},
                "Network Monitor": {"name": "Network Monitor", "status": "active", "desc": ""},
                "NexusProbe": {"name": "NexusProbe", "status": "idle", "desc": "Attach surface mapper"},
                "Fortress": {"name": "Fortress Defense", "status": "idle", "desc": ""},
                "AI Copilot": {"name": "AI Copilot", "status": "active", "desc": ""},
            }
        self.logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": f"AEGISQ Core \u2014 {len(self.modules)} modules ({'REAL ENGINE' if REAL_MODULES else 'MOCK'})"
        })

    async def run_scan_target(self, target_type: str) -> dict:
        """Run scan using real or mock engine."""
        self.scan_count += 1
        scan_id = f"SCAN-{self.scan_count:04d}"

        if REAL_MODULES and self.kernel:
            try:
                if target_type == "recon":
                    result = self.kernel.dispatch("recon", target="local")
                elif target_type == "vuln":
                    result = self.kernel.dispatch("vuln", target="local")
                elif target_type == "network":
                    result = self.kernel.dispatch("network", interface="eth0", mode="monitor")
                else:
                    result = self.kernel.dispatch("recon", target="local")
                summary = result.get("message", "Scan completed via shadow313 kernel")
                return {
                    "title": f"{scan_id} \u2014 {target_type.upper()} scan completed",
                    "summary": summary
                }
            except Exception as e:
                logger.error(f"Scan error: {e}")
                return {"title": f"{scan_id} \u2014 scan error", "summary": str(e)}

        # Mock fallback
        await asyncio.sleep(1)
        return {
            "title": f"{scan_id} \u2014 {target_type.upper()} scan completed",
            "summary": "Scanned 142 endpoints. 3 open ports. 1 vulnerability found (CVE-2026-2834). 0 threats active."
        }


state = AppState()


async def broadcast(data: dict):
    for ws in state.websockets.copy():
        try:
            await ws.send_json(data)
        except:
            state.websockets.discard(ws)


@ app.get("/api/stats")
async def get_stats():
    active = sum(1 for m in state.modules.values() if m["status"] == "active")
    return {
        "modules_active": active,
        "modules_total": len(state.modules),
        "threats_today": state.threat_count,
        "scans_total": state.scan_count,
        "engine": "REAL" if REAL_MODULES else "MOCK",
        "uptime": str(int(time.time() - state.start_time)) + "s"
    }


@ app.get("/api/modules")
async def get_modules():
    return list(state.modules.values())


@ app.get("/api/alerts")
async def get_alerts(limit: int = 10):
    return state.alerts[-limit:][::-1]


@ app.get("/api/logs")
async def get_logs(limit: int = 20):
    return state.logs[-limit:][::-1]


class ScanRequest(BaseModel):
    type: str


@ app.post("/api/scan")
async def run_scan(req: ScanRequest):
    result = await state.run_scan_target(req.type)
    state.logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"{result['title']}: scan executed"
    })
    await broadcast({
        "type": "log",
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"{result['title']}"
    })
    return result


@ app.post("/api/restart")
async def restart_backend():
    state.logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": "Backend restart requested"
    })
    return {"status": "ok"}


@ app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.websockets.discard(websocket)


@ app.get("/")
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path) as f:
        return HTMLResponse(f.read())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
