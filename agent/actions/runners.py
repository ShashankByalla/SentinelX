import requests, os, time
from agent.utils.logger import log

PLAYBOOK_DIR = os.path.join(os.getcwd(), "agent", "playbooks")

def _load_playbook(pb_id: str):
    import yaml
    p = os.path.join(PLAYBOOK_DIR, f"{pb_id}.yaml")
    with open(p, "r") as f:
        return yaml.safe_load(f)

def run_playbook(pb_id: str, context: dict):
    pb = _load_playbook(pb_id)
    results = []
    for step in pb.get("actions", []):
        t = step.get("type")
        if t == "http_post":
            url = step.get("url")
            try:
                r = requests.post(url, timeout=10)
                results.append({"ok": r.status_code < 300, "status": r.status_code, "text": r.text})
            except Exception as e:
                results.append({"ok": False, "error": str(e)})
        else:
            results.append({"ok": False, "out": f"unknown action {t}"})
        # small sleep between steps
        time.sleep(1)
    log.info({"event":"playbook_run", "pb": pb_id, "results": results})
    return {"ok": all(r.get("ok") for r in results), "results": results}
