from agent.connectors.health import probe_url
from agent.utils.logger import log

def verify_resolution(pb_id: str, context: dict):
    svc = context.get("service")
    port_map = {"app1":5001, "app2":5002}
    ok = probe_url(f"http://localhost:{port_map.get(svc,5000)}/health")
    log.info({"event":"verify", "service": svc, "ok": ok})
    return {"verified": ok}
