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
APP_VERSION = "1.2.0"
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
        # Minimal fallback
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
            # Skip malformed files but log
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
# Startup / Shutdown & background monitor
# -----------------------------
bg_thread = None
stop_monitor = threading.Event()

def _background_monitor():
    # lightweight periodic job: just logs heartbeat and can be extended to auto-detect
    while not stop_monitor.is_set():
        try:
            log.info({"event": "heartbeat", "uptime": uptime_seconds()})
        except Exception:
            pass
        stop_monitor.wait(30)  # every 30 seconds

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
# Welcome / Landing Page
# -----------------------------
@app.get("/", response_class=HTMLResponse, tags=["UI"])
def welcome():
    """Landing page (browser)"""
    return f"""
    <html>
      <head>
        <title>SentinelX Agent</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          html,body{{height:100%;margin:0;font-family:Inter, system-ui, Arial, sans-serif}}
          body{{display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0f1724,#1f2937);color:#e6eef8}}
          .card{{width:90%;max-width:900px;padding:36px;border-radius:12px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));box-shadow:0 10px 30px rgba(2,6,23,0.6)}}
          h1{{
            margin:0 0 10px 0;font-size:32px;color:#7ee3c0
          }}
          p{{margin:0 0 18px 0;color:#c7d2e0}}
          .row{{display:flex;gap:12px;flex-wrap:wrap;justify-content:center}}
          a.btn{{padding:10px 18px;border-radius:8px;background:#0ea5a5;color:#04292b;text-decoration:none;font-weight:600}}
          footer{{margin-top:20px;color:#98a8b9;font-size:13px;text-align:center}}
        </style>
      </head>
      <body>
        <div class="card">
          <h1>🚀 SentinelX Agent</h1>
          <p>AI-assisted incident detection and safe remediation engine. Use the interactive API docs or call endpoints directly.</p>
          <div class="row">
            <a class="btn" href="/docs">Open API Docs</a>
            <a class="btn" href="/health">Health</a>
            <a class="btn" href="/metrics">Prometheus Metrics</a>
            <a class="btn" href="/metrics/json">JSON Metrics</a>
            <a class="btn" href="/playbooks">Playbooks</a>
          </div>
          <footer>SentinelX Agent v{APP_VERSION} • Host: {HOSTNAME}</footer>
        </div>
      </body>
    </html>
    """

# -----------------------------
# Health
# -----------------------------
@app.get("/health", tags=["System"])
def health():
    """Liveness and basic info"""
    data = {"status": "healthy", "uptime_sec": uptime_seconds(), "hostname": HOSTNAME}
    log.info({"event": "health_check", "health": data})
    return data

# -----------------------------
# Metrics (JSON)
# -----------------------------
@app.get("/metrics/json", tags=["System"])
def metrics_json():
    """System metrics (JSON)"""
    metrics = gather_system_metrics()
    log.info({"event": "metrics_requested", "metrics_summary": {"cpu": metrics.get("cpu_percent")}})
    return JSONResponse(content=metrics)

# -----------------------------
# Metrics (Prometheus text)
# -----------------------------
@app.get("/metrics", response_class=PlainTextResponse, tags=["System"])
def metrics_prometheus():
    m = gather_system_metrics()
    # Build simple Prometheus exposition text
    lines = [
        "# HELP sentinelx_uptime_seconds Uptime of the SentinelX Agent in seconds",
        "# TYPE sentinelx_uptime_seconds gauge",
        f"sentinelx_uptime_seconds {m.get('uptime_seconds', 0)}",
        "# HELP sentinelx_cpu_percent CPU usage percent",
        "# TYPE sentinelx_cpu_percent gauge",
        f"sentinelx_cpu_percent {m.get('cpu_percent', 0) or 0}",
    ]
    mem = m.get("memory", {})
    if mem:
        lines += [
            "# HELP sentinelx_memory_used_mb Memory used in MB",
            "# TYPE sentinelx_memory_used_mb gauge",
            f"sentinelx_memory_used_mb {mem.get('used_mb', 0)}",
            "# HELP sentinelx_memory_percent Memory usage percent",
            "# TYPE sentinelx_memory_percent gauge",
            f"sentinelx_memory_percent {mem.get('percent', 0)}",
        ]
    disk = m.get("disk", {})
    if disk:
        lines += [
            "# HELP sentinelx_disk_used_gb Disk used in GB",
            "# TYPE sentinelx_disk_used_gb gauge",
            f"sentinelx_disk_used_gb {disk.get('used_gb', 0)}",
            "# HELP sentinelx_disk_percent Disk usage percent",
            "# TYPE sentinelx_disk_percent gauge",
            f"sentinelx_disk_percent {disk.get('percent', 0)}",
        ]
    lines += [
        "# HELP sentinelx_process_count Number of running processes",
        "# TYPE sentinelx_process_count gauge",
        f"sentinelx_process_count {m.get('process_count', 0) or 0}",
    ]
    return "\n".join(lines)

# -----------------------------
# Playbooks listing
# -----------------------------
@app.get("/playbooks", response_model=List[PlaybookSummary], tags=["Playbooks"])
def playbooks():
    """List available playbooks from agent/playbooks/*.yaml"""
    pbs = list_playbooks()
    return pbs

# -----------------------------
# Tail logs helper (for demo)
# -----------------------------
class TailRequest(BaseModel):
    path: str = Field(..., description="Relative path to log file (under demo/ or absolute)")
    lines: int = Field(200, description="Number of tail lines to return")

@app.post("/logs/tail", tags=["Debug"])
def tail_logs(req: TailRequest):
    """Return last N lines of a log file (demo helper)."""
    # restrict to demo dir unless absolute path and permitted
    path = req.path
    # Security: disallow path traversal
    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    # allow demo/ prefix or absolute
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    content = tail_file_logs(path, lines=req.lines)
    return {"path": path, "lines": req.lines, "content": content}

# -----------------------------
# Incident detect & resolve (core)
# -----------------------------
@app.post("/incident/detect", response_model=IncidentModel, tags=["Incidents"])
def detect(req: DetectRequest = Body(...)):
    """
    Detect an incident for a service:
    - probes service health
    - tails logs
    - returns signals + last logs
    """
    service = req.service
    env = req.env
    # demo mapping — replace for real integration
    port_map = {"app1": 5001, "app2": 5002}
    port = port_map.get(service, 5001)

    probe = probe_url(f"http://localhost:{port}/health")
    last_logs = tail_file_logs(os.path.join("demo", service, "app.log"), lines=200)

    db_cpu = 92 if "db timeout" in last_logs.lower() else 10

    incident = {"service": service, "env": env, "signals": {"health": probe, "db_cpu": db_cpu}, "last_logs": last_logs}
    log.info({"event": "incident_detected", "incident": incident})
    return incident

@app.post("/incident/resolve", tags=["Incidents"])
def resolve(req: ResolveRequest = Body(...)):
    """
    Resolve an incident by selecting and executing a playbook, then verify.
    """
    incident = req.incident
    decision = reason_and_select_playbook(incident)
    log.info({"event": "decision_made", "decision": decision, "incident_service": incident.get("service")})

    # safety: require manual approval for high-risk actions
    if decision.get("risk_score", 0) > 0.6:
        log.info({"event": "requires_approval", "decision": decision})
        return {"status": "needs_approval", "decision": decision}

    # execute playbook
    outcome = run_playbook(decision["playbook_id"], context=incident)
    verified = verify_resolution(decision["playbook_id"], context=incident)

    result = {"decision": decision, "outcome": outcome, "verified": verified}
    log.info({"event": "incident_resolved", "result": result})
    return result

# -----------------------------
# Simple health-check endpoint that also lists latest playbook
# -----------------------------
@app.get("/status", tags=["System"])
def status():
    """Combined status view for quick checks."""
    pbs = list_playbooks()
    return {
        "status": "ok",
        "uptime_sec": uptime_seconds(),
        "playbook_count": len(pbs),
        "hostname": HOSTNAME,
    }

# End of file
