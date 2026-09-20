import json
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.seo import sitemap_entries


class Command(BaseCommand):
    help = "Submit explicit significant published-page updates to IndexNow."

    def add_arguments(self, parser):
        parser.add_argument("--url", action="append", default=[])
        parser.add_argument("--all", action="store_true")

    def handle(self, *args, **options):
        key = settings.AIPEDIA_INDEXNOW_KEY
        if not key:
            raise CommandError("Set AIPEDIA_INDEXNOW_KEY before using IndexNow.")
        urls = options["url"]
        if options["all"]:
            urls.extend(url for url, _ in sitemap_entries())
        urls = sorted(set(urls))
        if not urls:
            raise CommandError("Pass --url or --all; submissions are never automatic.")
        payload = json.dumps({
            "host": settings.AIPEDIA_PUBLIC_ORIGIN.removeprefix("https://").removeprefix("http://"),
            "key": key,
            "keyLocation": f"{settings.AIPEDIA_PUBLIC_ORIGIN}/indexnow/{key}.txt",
            "urlList": urls,
        }).encode("utf-8")
        request = Request(
            "https://api.indexnow.org/indexnow",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            self.stdout.write(self.style.SUCCESS(f"IndexNow HTTP {response.status}: {len(urls)} URLs submitted."))
