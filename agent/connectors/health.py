import psutil
import time
import socket
import requests
import os

def probe_url(url: str, timeout=3):
    """Simple HTTP GET probe to check if a service URL is reachable."""
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _get_cpu_percent_fallback():
    """Fallback: Read CPU usage directly from /proc/stat if psutil fails."""
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
        parts = line.split()[1:]
        values = list(map(int, parts))
        idle = values[3]
        total = sum(values)

        time.sleep(1)  # wait 1s to measure delta
        with open("/proc/stat", "r") as f:
            line2 = f.readline()
        parts2 = line2.split()[1:]
        values2 = list(map(int, parts2))
        idle2 = values2[3]
        total2 = sum(values2)

        idle_delta = idle2 - idle
        total_delta = total2 - total
        cpu_usage = 100.0 * (1.0 - idle_delta / total_delta)
        return round(cpu_usage, 2)
    except Exception as e:
        return None


def collect_system_health():
    """Collects system health metrics safely with fallback."""
    try:
        # CPU %
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent == 0.0:  # sometimes psutil returns 0.0 inside containers
                cpu_percent = _get_cpu_percent_fallback()
        except Exception:
            cpu_percent = _get_cpu_percent_fallback()

        # Memory
        try:
            mem = psutil.virtual_memory()
            memory = {
                "total": int(mem.total),
                "available": int(mem.available),
                "used": int(mem.used),
                "percent": float(mem.percent)
            }
        except Exception:
            memory = {}

        # Disk
        try:
            disk = psutil.disk_usage("/")
            disk_info = {
                "total": int(disk.total),
                "used": int(disk.used),
                "free": int(disk.free),
                "percent": float(disk.percent)
            }
        except Exception:
            disk_info = {}

        # Processes
        try:
            process_count = len(psutil.pids())
        except Exception:
            process_count = None

        # Uptime
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = round(time.time() - boot_time, 2)
        except Exception:
            uptime_seconds = None

        # Hostname
        hostname = socket.gethostname()

        return {
            "uptime_seconds": uptime_seconds,
            "cpu_percent": cpu_percent,
            "memory": memory,
            "disk": disk_info,
            "process_count": process_count,
            "hostname": hostname
        }

    except Exception as e:
        return {"error": f"health_collection_failed: {str(e)}"}
