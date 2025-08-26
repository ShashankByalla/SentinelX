def reason_and_select_playbook(incident: dict) -> dict:
    logs = (incident.get("last_logs") or "").lower()
    db_cpu = float(incident.get("signals", {}).get("db_cpu", 0))
    if ("timeout" in logs or "econnrefused" in logs) and db_cpu > 80:
        return {
            "root_cause":"Database saturation causing connection timeouts",
            "confidence":0.8,
            "playbook_id":"pb-021-db-timeout",
            "risk_score":0.35,
            "summary":"DB CPU high; simulate scaling + restart app"
        }
    return {
        "root_cause":"Unknown - recommend safe restart",
        "confidence":0.4,
        "playbook_id":"pb-001-restart-app",
        "risk_score":0.2,
        "summary":"Restart app and re-check"
    }
