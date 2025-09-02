# agent/app.py
from fastapi import FastAPI, Body, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from agent.connectors.file_logs import tail_file_logs
from agent.connectors.health import probe_url
from agent.reasoner.reasoner import reason_and_select_playbook
from agent.actions.runners import run_playbook
from agent.actions.verify import verify_resolution
from agent.utils.logger import log
from agent.auto_resolver import AutoResolver   # 👈 new import
import time
import socket
import os
import glob
import yaml
import threading

# optional psutil (fallback if missing)
try:
    import psutil
except Exception:
    psutil = None

# -----------------------------
# App Initialization
# -----------------------------
start_time = time.time()
APP_VERSION = "1.4.0"
HOSTNAME = socket.gethostname()

app = FastAPI(
    title="SentinelX Agent",
    version=APP_VERSION,
    description="SentinelX — AI-powered incident detection & resolution agent.",
    docs_url="/docs",
    redoc_url=None,
)

# CORS (open for demo; tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# -----------------------------
# Initialize AutoResolver
# -----------------------------
resolver = AutoResolver()

# -----------------------------
# Pydantic models
# -----------------------------
class DetectRequest(BaseModel):
    service: str = Field(..., description="Service name (e.g., app1, app2)")
    env: str = Field("dev", description="Environment name (dev/stage/prod)")

class IncidentModel(BaseModel):
    service: str
    env: str
    signals: Dict[str, Any]
    last_logs: str

class ResolveRequest(BaseModel):
    incident: Dict[str, Any]

class PlaybookSummary(BaseModel):
    id: str
    name: Optional[str]
    risk: Optional[float]

# -----------------------------
# Helpers
# -----------------------------
def uptime_seconds() -> float:
    return round(time.time() - start_time, 2)

def gather_system_metrics() -> Dict[str, Any]:
    if psutil:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        pcount = len(psutil.pids())
        return {
            "uptime_seconds": uptime_seconds(),
            "cpu_percent": cpu,
            "memory": {
                "total_mb": round(mem.total / (1024 * 1024), 2),
                "used_mb": round(mem.used / (1024 * 1024), 2),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "percent": disk.percent,
            },
            "process_count": pcount,
            "hostname": HOSTNAME,
        }
    else:
        return {
            "uptime_seconds": uptime_seconds(),
            "cpu_percent": None,
            "memory": {},
            "disk": {},
            "process_count": None,
            "hostname": HOSTNAME,
        }

def list_playbooks() -> List[PlaybookSummary]:
    pb_dir = os.path.join(os.getcwd(), "agent", "playbooks")
    if not os.path.isdir(pb_dir):
        return []
    pbs = []
    for path in glob.glob(os.path.join(pb_dir, "*.yaml")) + glob.glob(os.path.join(pb_dir, "*.yml")):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            pbs.append(PlaybookSummary(id=data.get("id") or os.path.splitext(os.path.basename(path))[0],
                                       name=data.get("name"),
                                       risk=data.get("risk")))
        except Exception:
            log.error({"event": "playbook_load_failed", "path": path})
    return pbs

# -----------------------------
# Error handlers
# -----------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.error({"event": "validation_error", "errors": exc.errors(), "path": str(request.url)})
    return JSONResponse(status_code=422, content={"error": "Invalid request", "details": exc.errors()})

# -----------------------------
# Background monitor (auto-heal)
# -----------------------------
bg_thread = None
stop_monitor = threading.Event()

def _background_monitor():
    while not stop_monitor.is_set():
        try:
            metrics = gather_system_metrics()
            log.info({"event": "heartbeat", "uptime": uptime_seconds(), "cpu": metrics.get("cpu_percent")})

            incident = {"service": "system", "env": os.getenv("ENV", "prod"), "signals": metrics, "last_logs": ""}
            decision = reason_and_select_playbook(incident)
            log.info({"event": "auto_decision", "decision": decision})

            if decision.get("risk_score", 0) <= 0.6:
                outcome = run_playbook(decision["playbook_id"], context=incident)
                resolution = resolver.resolve(decision["playbook_id"])   # 👈 new: auto-resolve
                verified = verify_resolution(decision["playbook_id"], context=incident)
                log.info({
                    "event": "auto_resolution",
                    "decision": decision,
                    "outcome": outcome,
                    "resolver": resolution,
                    "verified": verified
                })
            else:
                log.info({"event": "auto_skip_high_risk", "decision": decision})

        except Exception as e:
            log.error({"event": "monitor_error", "error": str(e)})

        stop_monitor.wait(30)

@app.on_event("startup")
def startup_event():
    global bg_thread
    log.info({"event": "startup", "hostname": HOSTNAME})
    stop_monitor.clear()
    bg_thread = threading.Thread(target=_background_monitor, daemon=True)
    bg_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    stop_monitor.set()
    if bg_thread and bg_thread.is_alive():
        bg_thread.join(timeout=2)
    log.info({"event": "shutdown", "hostname": HOSTNAME})

# -----------------------------
# Endpoints (UI, health, metrics, logs, incidents)
# -----------------------------
# ... 👇 keep everything else identical to your current file
# (welcome page, /health, /metrics, /playbooks, /logs/tail, etc.)

@app.post("/incident/resolve", tags=["Incidents"])
def resolve(req: ResolveRequest = Body(...)):
    incident = req.incident
    decision = reason_and_select_playbook(incident)
    log.info({"event": "decision_made", "decision": decision, "incident_service": incident.get("service")})

    if decision.get("risk_score", 0) > 0.6:
        log.info({"event": "requires_approval", "decision": decision})
        return {"status": "needs_approval", "decision": decision}

    outcome = run_playbook(decision["playbook_id"], context=incident)
    resolution = resolver.resolve(decision["playbook_id"])   # 👈 auto-heal here too
    verified = verify_resolution(decision["playbook_id"], context=incident)

    result = {"decision": decision, "outcome": outcome, "resolver": resolution, "verified": verified}
    log.info({"event": "incident_resolved", "result": result})
    return result
