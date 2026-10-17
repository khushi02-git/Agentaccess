import json
import time
from datetime import datetime

import psutil


def get_cpu():
    # Measured over 1 second; a single instant reading is meaningless
    return psutil.cpu_percent(interval=1)


def get_ram():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / 1024**3, 1),
        "used_gb": round(mem.used / 1024**3, 1),
        "percent": mem.percent,
    }


def get_disk():
    # Change "C:\\" if you want to watch another drive
    disk = psutil.disk_usage("C:\\")
    return {"percent": disk.percent}


def get_processes(limit=10):
    procs = list(psutil.process_iter(["pid", "name"]))
    cores = psutil.cpu_count()

    # Pass 1: the first cpu_percent() call always returns 0.0,
    # so this call only starts the measurement
    for p in procs:
        try:
            p.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(1)

    # Pass 2: now each process has a real CPU reading
    results = []
    for p in procs:
        try:
            results.append({
                "pid": p.pid,
                "name": p.name(),
                "cpu_percent": round(p.cpu_percent(interval=None) / cores, 1),
                "memory_mb": round(p.memory_info().rss / 1024**2, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # process ended, or Windows refused access

    results.sort(key=lambda r: r["memory_mb"], reverse=True)
    return results[:limit]


def get_system_stats():
    return {
        "cpu_percent": get_cpu(),
        "ram": get_ram(),
        "disk": get_disk(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "processes": get_processes(),
    }


if __name__ == "__main__":
    print(json.dumps(get_system_stats(), indent=2))