"""Read-only AIpediya process snapshot for ``tools/server.py metrics``.

Sent to the configured host over stdin. It reads only the `aipedia` Supervisor
program, its /proc entries, and files inside /srv/aipedia. System load is
reported solely as shared-host context, never attributed to AIpediya.
"""

import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path


ROOT = Path("/srv/aipedia")
DB = ROOT / "data/aipedia.sqlite3"
SUPERVISOR = ROOT / "supervisord.conf"


def process_snapshot(pid):
    proc = Path("/proc") / str(pid)
    stat = (proc / "stat").read_text().rsplit(") ", 1)[1].split()
    # Fields after comm start at Linux stat field 3.
    status = {}
    for line in (proc / "status").read_text().splitlines():
        key, _, value = line.partition(":")
        if key in {"VmRSS", "VmSize", "Threads", "voluntary_ctxt_switches", "nonvoluntary_ctxt_switches"}:
            status[key] = value.strip()
    thread_ticks = {}
    for task in (proc / "task").iterdir():
        try:
            fields = (task / "stat").read_text().rsplit(") ", 1)[1].split()
            thread_ticks[task.name] = int(fields[11]) + int(fields[12])
        except (OSError, ValueError):
            continue
    # Some containers deny root ptrace-style /proc reads without CAP_SYS_PTRACE.
    # The service owner may read its own counters; restore the original euid.
    original_euid = os.geteuid()
    try:
        os.seteuid(proc.stat().st_uid)
        io = {}
        try:
            for line in (proc / "io").read_text().splitlines():
                key, _, value = line.partition(":")
                if key in {"read_bytes", "write_bytes", "rchar", "wchar", "syscr", "syscw"}:
                    io[key] = int(value.strip())
        except PermissionError:
            pass
        sockets = 0
        sqlite_fds = 0
        try:
            fds = list((proc / "fd").iterdir())
            for fd in fds:
                try:
                    target = os.readlink(fd)
                except OSError:
                    continue
                sockets += target.startswith("socket:[")
                sqlite_fds += target.startswith(str(DB))
        except PermissionError:
            fds = []
    finally:
        os.seteuid(original_euid)
    return {
        "pid": pid,
        "cpu_ticks": int(stat[11]) + int(stat[12]),
        "minor_faults": int(stat[7]),
        "major_faults": int(stat[9]),
        "start_ticks": int(stat[19]),
        "status": status,
        "thread_ticks": thread_ticks,
        "io": io,
        "file_descriptors": len(fds) if fds else None,
        "socket_descriptors": sockets,
        "sqlite_descriptors": sqlite_fds,
    }


def log_files():
    log_root = ROOT / "logs"
    if not log_root.is_dir():
        return []
    entries = []
    for path in log_root.rglob("*"):
        if not path.is_file() or len(entries) >= 50:
            continue
        stat = path.stat()
        entries.append({"path": str(path.relative_to(ROOT)), "bytes": stat.st_size,
                        "modified_unix": stat.st_mtime})
    return entries


def app_error_summary():
    path = ROOT / "logs/app-error.log"
    if not path.is_file():
        return {"available": False}
    with path.open("rb") as source:
        source.seek(max(0, path.stat().st_size - 1024 * 1024))
        lines = source.read().decode("utf-8", errors="replace").splitlines()
    categories = Counter()
    route_roots = Counter()
    for line in lines:
        if "Not Found:" in line:
            categories["404_not_found"] += 1
            match = re.search(r"Not Found:\s*/([^/?\s]+)", line)
            if match:
                component = match.group(1)
                route_roots[component if component in {
                    "es", "ru", "tools", "models", "static", "sitemap.xml", "robots.txt"
                } else "other"] += 1
        elif "Internal Server Error" in line:
            categories["500_internal_error"] += 1
        elif "Task queue depth" in line:
            categories["waitress_queue_depth"] += 1
        elif "Traceback" in line:
            categories["traceback"] += 1
    sample = []
    for line in lines[-8:]:
        safe = re.sub(r"https?://\S+", "<url>", line)
        safe = re.sub(r"Not Found:\s*/\S+", "Not Found: /<path>", safe)
        sample.append(safe[:200])
    return {"available": True, "sample_bytes": min(path.stat().st_size, 1024 * 1024),
            "lines": len(lines), "categories": categories, "not_found_route_roots": route_roots,
            "redacted_tail": sample}


def app_error_delta(offset):
    path = ROOT / "logs/app-error.log"
    if not path.is_file() or path.stat().st_size < offset:
        return {"available": False, "reason": "absent or rotated during sample"}
    size = path.stat().st_size
    with path.open("rb") as source:
        source.seek(offset)
        data = source.read(min(size - offset, 1024 * 1024))
    lines = data.decode("utf-8", errors="replace").splitlines()
    routes = Counter()
    unique_404 = set()
    queue = 0
    for line in lines:
        match = re.search(r"Not Found:\s*(/\S+)", line)
        if match:
            path_only = match.group(1).split("?", 1)[0]
            unique_404.add(path_only)
            first = path_only.strip("/").split("/", 1)[0]
            routes[first if first in {"es", "ru", "models", "tools", "static"} else "other"] += 1
        queue += "Task queue depth" in line
    return {"available": True, "bytes_appended": size - offset,
            "truncated": size - offset > len(data), "404_count": sum(routes.values()),
            "404_unique_paths": len(unique_404), "404_route_roots": routes,
            "waitress_queue_warnings": queue}


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    if seconds not in {5, 10, 30}:
        raise SystemExit("unsupported metric sample length")
    result = subprocess.run(["supervisorctl", "-c", str(SUPERVISOR), "status", "aipedia"],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise SystemExit("AIpediya Supervisor status failed: " + result.stderr.strip())
    match = re.search(r"\bRUNNING\s+pid\s+(\d+)", result.stdout)
    if not match:
        raise SystemExit("AIpediya is not RUNNING: " + result.stdout.strip())
    pid = int(match.group(1))
    error_log = ROOT / "logs/app-error.log"
    error_offset = error_log.stat().st_size if error_log.is_file() else 0
    start = time.monotonic()
    before = process_snapshot(pid)
    time.sleep(seconds)
    after = process_snapshot(pid)
    elapsed = time.monotonic() - start
    ticks = os.sysconf("SC_CLK_TCK")
    uptime = time.clock_gettime(time.CLOCK_BOOTTIME) - after["start_ticks"] / ticks
    sizes = {}
    for path in (DB, DB.with_name(DB.name + "-wal"), DB.with_name(DB.name + "-shm")):
        sizes[path.name] = path.stat().st_size if path.exists() else 0
    io_delta = {key: after["io"][key] - before["io"][key] for key in after["io"]}
    thread_cpu = {tid: round(100 * (value - before["thread_ticks"].get(tid, value)) / ticks / elapsed, 2)
                  for tid, value in after["thread_ticks"].items()}
    report = {
        "service": "aipedia", "supervisor": result.stdout.strip(),
        "sample_seconds": elapsed, "pid": pid, "uptime_seconds": uptime,
        "cpu_percent_one_core": round(100 * (after["cpu_ticks"] - before["cpu_ticks"]) / ticks / elapsed, 2),
        "rss": after["status"].get("VmRSS"), "virtual_memory": after["status"].get("VmSize"),
        "threads": after["status"].get("Threads"),
        "thread_cpu_percent_one_core": thread_cpu,
        "file_descriptors": after["file_descriptors"],
        "socket_descriptors": after["socket_descriptors"],
        "sqlite_descriptors": after["sqlite_descriptors"],
        "minor_faults_delta": after["minor_faults"] - before["minor_faults"],
        "major_faults_delta": after["major_faults"] - before["major_faults"],
        "io_delta": io_delta, "sqlite_bytes": sizes,
        "aipedia_logs": log_files(),
        "app_error_summary": app_error_summary(),
        "app_error_delta": app_error_delta(error_offset),
        "shared_host_load_average": os.getloadavg(),
        "network_bytes_per_process": "unavailable from standard /proc counters",
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
