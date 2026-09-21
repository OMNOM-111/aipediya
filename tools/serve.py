import argparse
import atexit
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
from django.conf import settings
from aipedia.wsgi import application
from waitress import serve


def write_pid_file():
    raw = os.environ.get("AIPEDIA_PID_FILE")
    if not raw:
        return
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(os.getpid()), encoding="utf-8")

    def cleanup():
        try:
            if path.read_text(encoding="utf-8").strip() == str(os.getpid()):
                path.unlink()
        except OSError:
            pass

    atexit.register(cleanup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18810)
    args = parser.parse_args()
    if settings.AIPEDIA_ENV == "local" and os.environ.get("AIPEDIA_TRUST_PROXY") == "1":
        raise SystemExit("Local must not enable AIPEDIA_TRUST_PROXY")
    write_pid_file()
    # Loopback is the only bind for Local; Production keeps the same origin bind
    # behind its existing dedicated tunnel.
    options = {"host": "127.0.0.1", "port": args.port, "threads": 4, "max_request_body_size": 65536}
    if os.environ.get("AIPEDIA_TRUST_PROXY") == "1":
        options.update(trusted_proxy="127.0.0.1", trusted_proxy_headers="x-forwarded-proto")
    serve(application, **options)
