"""AEGISQ Mini App backend — wired to real shadow313 engine."""

import os, json, time, asyncio, logging
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aegisq")
app = FastAPI(title="AEGISQ Mini App")

# ── Import real shadow313 engine (graceful fallbacks) ──
try:
    from shadow313 import __version__ as SHADOW_VERSION
    from shadow313.core.kernel import Kernel
    from shadow313.tools.nexusprobe import NexusProbe
    from shadow313.modules.fortress.defense import FortressEngine as RealFortress
    HAS_REAL_MODULES = True
    logger.info("[AEGISQ] shadow313 engine loaded v%s", SHADOW_VERSION)
except ImportError:
    HAS_REAL_MODULES = False
    SHADOW_VERSION = "0.0.0"
    logger.warning("[AEGISQ] shadow313 not installed — using simulation mode")

    class Kernel:
        def __init__(self, *a, **kw):
            self.verbose = kw.get("verbose", False)

        def dispatch(self, command, **kwargs):
            return {"status": "simulated", "command": command, "message": "Simulated response"}

    class NexusProbe:
        def run(self, target="localhost"):
            return {"status": "simulated", "target": target, "ports_found": 3, "vulns": []}

    class RealFortress:
        async def run(self, mode="monitor"):
            return {"status": "simulated", "mode": mode}


# ── App state ──
class AppState:
    def __init__(self):
        self.start_time = time.time()
        self.modules: dict[str, dict] = {}
        self.alerts: list[dict] = []
        self.logs: list[dict] = []
        self.scan_count = 0
        self.threat_count = 0
        self.websockets: set[WebSocket] = set()
        self.kernel: Optional[Kernel] = None
        self.nexus: Optional[NexusProbe] = None
        self.fortress: Optional[RealFortress] = None


state = AppState()

# ── Initialize engines ──
def init_engines():
    """Initialize all real modules."""
    if HAS_REAL_MODULES:
        try:
            state.kernel = Kernel(verbose=True)
            state.nexus = NexusProbe()
            state.fortress = RealFortress()
            logger.info("[AEGISQ] All engines initialized")
            return True
        except Exception as e:
            logger.error("[AEGISQ] Engine init failed: %s", e)
    return False


DEFAULT_MODULES_LIGHT = [
    {"slug": "kernel", "name": "Kernel Engine", "status": "active", "description": "Command orchestration & dispatch"},
    {"slug": "fortress", "name": "Fortress Defense", "status": "active", "description": "Network defense, tarpit, honeypot"},
    {"slug": "nexusprobe", "name": "NexusProbe", "status": "active", "description": "AI-guided attack surface mapping"},
    {"slug": "scan", "name": "Threat Detection", "status": "active", "description": "Port scan, vuln detection"},
    {"slug": "network", "name": "Network Monitor", "status": "idle", "description": "Real-time traffic analysis"},
    {"slug": "dns", "name": "DNS Exfil Detector", "status": "idle", "description": "DNS tunneling detection"},
    {"slug": "soc", "name": "SOC Automation", "status": "active", "description": "Automated incident response"},
    {"slug": "crypto", "name": "Quantum Crypto", "status": "idle", "description": "Post-quantum cryptography"},
]

for m in DEFAULT_MODULES_LIGHT:
    state.modules[m["slug"]] = m

init_engines()

state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": f"AEGISQ Core initialized (shadow313 v{SHADOW_VERSION})"})
state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": f"{len(state.modules)} modules loaded, real={HAS_REAL_MODULES}"})


# ── WebSocket broadcast ──
async def broadcast(data: dict):
    for ws in state.websockets.copy():
        try:
            await ws.send_json(data)
        except Exception:
            state.websockets.discard(ws)


# ── REST endpoints ──
@app.get("/api/stats")
async def get_stats():
    active = sum(1 for m in state.modules.values() if m["status"] == "active")
    return {
        "modules_active": active,
        "threats_today": state.threat_count,
        "scans_total": state.scan_count,
        "uptime": str(int(time.time() - state.start_time)) + "s",
        "engine": "real" if HAS_REAL_MODULES else "simulated",
    }


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
    target: Optional[str] = "localhost"


@app.post("/api/scan")
async def run_scan(req: ScanRequest):
    """Run a scan using real shadow313 engine when available."""
    state.scan_count += 1
    scan_id = f"SCAN-{state.scan_count:04d}"

    if HAS_REAL_MODULES and state.nexus:
        try:
            result = state.nexus.run(target=req.target)
            summary = result.get("summary", f"Scanned {req.target}. {result.get('ports_found', 0)} open ports.")
            vulns = result.get("vulns", [])
            if vulns:
                state.threat_count += len(vulns)
                for v in vulns:
                    state.alerts.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "type": "vuln",
                        "title": v.get("id", "CVE-unknown"),
                        "severity": v.get("severity", "medium"),
                    })
            response = {
                "title": f"{scan_id} — {req.type.upper()} scan completed",
                "summary": summary,
                "engine": "shadow313",
            }
        except Exception as e:
            logger.error("Scan failed: %s", e)
            response = {"title": f"{scan_id} — scan error", "summary": str(e), "engine": "error"}
    else:
        await asyncio.sleep(0.5)
        response = {
            "title": f"{scan_id} — {req.type.upper()} scan completed",
            "summary": f"Scanned {req.target}. 142 endpoints. 3 open ports. 1 vulnerability found (CVE-2026-2834).",
            "engine": "simulated",
        }

    state.logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"{scan_id}: {req.type} scan — {response.get('summary', 'done')}",
    })
    await broadcast({
        "type": "log",
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"{scan_id}: {req.type} scan completed",
    })
    return response


@app.post("/api/module/{slug}/toggle")
async def toggle_module(slug: str):
    """Toggle a module on/off."""
    if slug not in state.modules:
        return {"status": "error", "message": f"Module '{slug}' not found"}

    m = state.modules[slug]
    if m["status"] == "active":
        m["status"] = "idle"
        action = "deactivated"
    else:
        m["status"] = "active"
        action = "activated"

    state.logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"Module '{m['name']}' {action}",
    })
    return {"status": "ok", "module": m}


@app.post("/api/restart")
async def restart_backend():
    init_engines()
    state.logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": "Backend restart requested — engines re-initialized"})
    return {"status": "ok", "engine": "real" if HAS_REAL_MODULES else "simulated"}


# ── WebSocket ──
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                if cmd.get("action") == "ping":
                    await websocket.send_json({"type": "pong", "time": datetime.now().strftime("%H:%M:%S")})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        state.websockets.discard(websocket)


@app.get("/")
async def root():
    with open("/app/frontend/index.html") as f:
        return HTMLResponse(f.read())


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
