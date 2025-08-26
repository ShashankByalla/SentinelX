import os
def tail_file_logs(path: str, lines: int = 200):
    if not os.path.exists(path):
        return ""
    # Efficient tail: read file and return last N lines
    with open(path, "r", errors="ignore") as f:
        content = f.read().splitlines()
    return "\\n".join(content[-lines:])
