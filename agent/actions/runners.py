import requests, os, time, subprocess
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

        # -----------------------------
        # 1. HTTP POST action
        # -----------------------------
        if t == "http_post":
            url = step.get("url")
            try:
                r = requests.post(url, timeout=10)
                results.append({
                    "ok": r.status_code < 300,
                    "status": r.status_code,
                    "text": r.text
                })
            except Exception as e:
                results.append({
                    "ok": False,
                    "error": str(e)
                })

        # -----------------------------
        # 2. Restart service (systemctl)
        # -----------------------------
        elif t == "restart_service":
            service = step.get("service")
            try:
                subprocess.run(["systemctl", "restart", service], check=True)
                results.append({
                    "ok": True,
                    "service": service,
                    "action": "restart",
                    "result": "success"
                })
            except subprocess.CalledProcessError as e:
                results.append({
                    "ok": False,
                    "service": service,
                    "action": "restart",
                    "result": "failed",
                    "error": str(e)
                })

        # -----------------------------
        # 3. Shell command execution
        # -----------------------------
        elif t == "shell":
            cmd = step.get("command")
            try:
                out = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, check=True
                )
                results.append({
                    "ok": True,
                    "command": cmd,
                    "stdout": out.stdout.strip(),
                    "stderr": out.stderr.strip()
                })
            except subprocess.CalledProcessError as e:
                results.append({
                    "ok": False,
                    "command": cmd,
                    "stdout": e.stdout,
                    "stderr": e.stderr,
                    "error": str(e)
                })

        # -----------------------------
        # 4. Unknown action
        # -----------------------------
        else:
            results.append({
                "ok": False,
                "out": f"unknown action {t}"
            })

        # small sleep between steps
        time.sleep(1)

    log.info({"event": "playbook_run", "pb": pb_id, "results": results})
    return {
        "ok": all(r.get("ok") for r in results),
        "results": results
    }
