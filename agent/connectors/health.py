import requests
def probe_url(url: str, timeout=3):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False
