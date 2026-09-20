"""Read-only origin inspection. Run on the intended Linux host before provisioning."""
import json
import platform
import shutil
import socket
from pathlib import Path


def inspect():
    init_path = Path("/proc/1/comm")
    with socket.socket() as sock:
        sock.settimeout(1)
        occupied = sock.connect_ex(("127.0.0.1", 18810)) == 0
    disk = shutil.disk_usage(Path.home())
    return {"os": platform.system(), "init": init_path.read_text().strip() if init_path.exists() else "not Linux",
            "supervisorctl_present": bool(shutil.which("supervisorctl")),
            "cloudflared_present": bool(shutil.which("cloudflared")),
            "port_18810_listening": occupied, "home_disk_free_gib": round(disk.free / 1024**3, 1),
            "ready_for_deploy": False,
            "remaining": ["Confirm Supervisor include path and process baseline", "Confirm domain and dedicated tunnel", "Confirm RAM, disk location, backup and editor access"]}


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2))
