from django.core.management.base import BaseCommand, CommandError

from catalog.discovery import allowed_host, enqueue
from catalog.locale_urls import split
from catalog.seo import sitemap_urlsets


class Command(BaseCommand):
    help = (
        "Queue explicit URL changes in the discovery outbox (nothing is sent here; "
        "indexnow_dispatch submits them). --all queues every indexable URL from the readiness registry."
    )

    def add_arguments(self, parser):
        parser.add_argument("--url", action="append", default=[])
        parser.add_argument("--all", action="store_true",
                            help="Only after a genuine catalog-wide change (e.g. a URL-architecture release).")
        parser.add_argument("--remove", action="store_true", help="Queue the given --url values as removals.")

    def handle(self, *args, **options):
        from django.conf import settings

        urls = list(options["url"])
        if options["all"]:
            urls.extend(entry["loc"] for entries in sitemap_urlsets().values() for entry in entries)
        urls = sorted(set(urls))
        if not urls:
            raise CommandError("Pass --url or --all; submissions are never automatic.")
        action = "remove" if options["remove"] else "upsert"
        origin = settings.AIPEDIA_PUBLIC_ORIGIN
        queued = 0
        for url in urls:
            if not allowed_host(url):
                raise CommandError(f"Not an AIpediya public URL: {url}")
            path = url[len(origin):].split("?", 1)[0] or "/"
            lang, neutral, _redirect = split(path)
            enqueue(neutral, lang or "en", action, "manual")
            queued += 1
        self.stdout.write(self.style.SUCCESS(f"Queued {queued} URL(s); run indexnow_dispatch to submit."))
