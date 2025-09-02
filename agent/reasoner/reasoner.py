def reason_and_select_playbook(incident: dict) -> dict:
    """
    Decide which playbook to run based on incident data.
    Looks at system health signals (CPU, Memory, Disk, Logs).
    """

    logs = (incident.get("last_logs") or "").lower()
    signals = incident.get("signals", {})

    cpu = float(signals.get("cpu_percent", 0))
    mem = float(signals.get("memory", {}).get("percent", 0))
    disk = float(signals.get("disk", {}).get("percent", 0))

    # --- Rules ---

    # 1. If DB connection errors + CPU high
    if ("timeout" in logs or "econnrefused" in logs) and cpu > 80:
        return {
            "root_cause": "Database saturation causing connection timeouts",
            "confidence": 0.85,
            "playbook_id": "pb-021-db-timeout",
            "risk_score": 0.45,
            "summary": "DB CPU high; simulate scaling + restart app"
        }

    # 2. If CPU usage is very high → run high CPU playbook
    if cpu > 85:
        return {
            "root_cause": "High CPU utilization detected",
            "confidence": 0.9,
            "playbook_id": "pb-003-high-cpu",   # 👈 New playbook
            "risk_score": 0.5,
            "summary": f"CPU at {cpu}%, restarting sentinelx + nginx"
        }

    # 3. If Memory usage is too high
    if mem > 85:
        return {
            "root_cause": "Memory pressure detected",
            "confidence": 0.75,
            "playbook_id": "pb-001-restart-app",
            "risk_score": 0.35,
            "summary": f"Memory at {mem}%, triggering restart"
        }

    # 4. If Disk nearly full
    if disk > 90:
        return {
            "root_cause": "Disk usage critical",
            "confidence": 0.9,
            "playbook_id": "pb-001-restart-app",
            "risk_score": 0.5,
            "summary": f"Disk usage at {disk}%, triggering cleanup/restart"
        }

    # Default fallback
    return {
        "root_cause": "Unknown - recommend safe restart",
        "confidence": 0.5,
        "playbook_id": "pb-001-restart-app",
        "risk_score": 0.2,
        "summary": "Restart app and re-check"
    }
