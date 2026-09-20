"""Read-only checks for the URLs stored in this local catalog."""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django
django.setup()
from catalog.models import Source, Service


def check(url):
    try:
        with urlopen(Request(url, headers={"User-Agent": "AIpedia-source-check/0.1"}), timeout=20) as response:
            return {"url": url, "status": response.status, "final": response.url}
    except HTTPError as error:
        return {"url": url, "status": error.code}
    except Exception as error:
        return {"url": url, "status": "unverified", "error": type(error).__name__}


if __name__ == "__main__":
    urls = sorted(set(Source.objects.values_list("url", flat=True)) | set(Service.objects.values_list("url", flat=True)))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, urls))
    print(json.dumps(results, indent=2))
