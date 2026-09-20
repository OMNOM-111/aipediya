import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
from aipedia.wsgi import application
from waitress import serve

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18810)
    args = parser.parse_args()
    # The loopback bind is also the trust boundary for a dedicated tunnel.
    options = {"host": "127.0.0.1", "port": args.port, "threads": 4, "max_request_body_size": 65536}
    if os.environ.get("AIPEDIA_TRUST_PROXY") == "1":
        options.update(trusted_proxy="127.0.0.1", trusted_proxy_headers="x-forwarded-proto")
    serve(application, **options)
