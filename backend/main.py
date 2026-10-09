"""AEGISQ Mini App Backend — proxies detection + WebSocket alerts."""
import json, os, asyncio, logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("aegisq-miniapp")

DETECTOR_URL = os.getenv("DETECTOR_URL", "http://detector:8000")

# Track connected websocket clients
connected_clients: set[WebSocket] = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AEGISQ Mini App Backend starting...")
    yield
    logger.info("Shutting down.")

app = FastAPI(title="AEGISQ Mini App API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "aegisq-miniapp"}

@app.get("/detector/health")
async def detector_health():
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{DETECTOR_URL}/health", timeout=5)
            return r.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

@app.post("/detector/detect")
async def run_detection(data: dict = None):
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{DETECTOR_URL}/detect", json=data or {}, timeout=30)
            return r.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

@app.get("/detector/report")
async def get_report():
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{DETECTOR_URL}/report", timeout=30)
            return r.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"WebSocket client connected ({len(connected_clients)} total)")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected ({len(connected_clients)} remaining)")

async def broadcast(message: dict):
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    connected_clients -= dead

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
