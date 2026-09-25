"""Send pending discovery events to IndexNow (GSD-08).

Real submission requires ALL of: AIPEDIA_ENV=production,
AIPEDIA_INDEXNOW_ENABLED=1, AIPEDIA_INDEXNOW_KEY and ``--send``. Otherwise the
command is a dry run that reports what would be sent and changes nothing.
Local therefore never sends. There is no scheduler; run it deliberately (or
from a Production timer after the owner enables it).

Per run: pending events due now, host allowlist, live-state gate (an upsert
URL must answer 200 and a removed URL 404/410 on Production before it is
announced), one POST of at most ``--batch`` URLs (IndexNow allows 10,000).
Responses: 200/202 -> sent; 400/422 -> failed (not retried); 403 -> run
aborted, events stay pending (key problem); 429 and 5xx/network -> retried
with exponential backoff up to ``--max-attempts``, then failed.
"""
import json
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.discovery import allowed_host
from catalog.models import DiscoveryEvent

INDEXNOW_MAX = 10_000


def http_post(url, payload, timeout=20):
    request = Request(url, data=payload, method="POST",
                      headers={"Content-Type": "application/json; charset=utf-8",
                               "User-Agent": "AIpediya-IndexNow/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.headers.get("Retry-After")
    except HTTPError as error:
        return error.code, error.headers.get("Retry-After") if error.headers else None


def http_status(url, timeout=15):
    request = Request(url, method="GET", headers={"User-Agent": "AIpediya-IndexNow-livecheck/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status
    except HTTPError as error:
        return error.code


class Command(BaseCommand):
    help = "Dispatch pending discovery events to IndexNow (dry run unless explicitly enabled in Production)."

    # Injection points for tests; never replaced in production code.
    post = staticmethod(http_post)
    probe = staticmethod(http_status)

    def add_arguments(self, parser):
        parser.add_argument("--send", action="store_true", help="Really submit (Production + enabled only).")
        parser.add_argument("--batch", type=int, default=1000)
        parser.add_argument("--max-attempts", type=int, default=6)
        parser.add_argument("--no-live-check", action="store_true",
                            help="Skip the Production live-state gate (tests only).")

    def handle(self, *args, **options):
        batch = max(1, min(options["batch"], INDEXNOW_MAX))
        key = settings.AIPEDIA_INDEXNOW_KEY
        can_send = (
            options["send"] and settings.AIPEDIA_ENV == "production"
            and getattr(settings, "AIPEDIA_INDEXNOW_ENABLED", False) and bool(key)
        )
        now = timezone.now()
        due = list(DiscoveryEvent.objects.filter(state="pending").filter(
            next_attempt__isnull=True) | DiscoveryEvent.objects.filter(state="pending", next_attempt__lte=now))
        due.sort(key=lambda event: (event.created, event.pk))
        if not can_send:
            self.stdout.write(f"DRY RUN (send disabled): {len(due)} pending event(s) due; nothing sent.")
            for event in due[:batch]:
                self.stdout.write(f"  would {event.action}: {event.url} [{event.reason}]")
            return
        ready, deferred = [], 0
        for event in due:
            if len(ready) >= batch:
                break
            if not allowed_host(event.url):
                self._finish(event, "skipped", None, "host-not-allowed")
                continue
            if not options["no_live_check"]:
                status = self.probe(event.url)
                live = status == 200 if event.action == "upsert" else status in (404, 410)
                if not live:
                    self._retry(event, options["max_attempts"], status, "production-state-not-live")
                    deferred += 1
                    continue
            ready.append(event)
        if not ready:
            self.stdout.write(f"Nothing to send ({deferred} deferred).")
            return
        host = settings.AIPEDIA_PUBLIC_ORIGIN.split("://", 1)[-1]
        payload = json.dumps({
            "host": host, "key": key,
            "keyLocation": f"{settings.AIPEDIA_PUBLIC_ORIGIN}/indexnow/{key}.txt",
            "urlList": [event.url for event in ready],
        }).encode("utf-8")
        try:
            status, retry_after = self.post(settings.AIPEDIA_INDEXNOW_ENDPOINT, payload)
        except (URLError, OSError) as error:
            status, retry_after = None, None
            reason = f"network: {error}"[:300]
        else:
            reason = f"HTTP {status}"
        if status in (200, 202):
            with transaction.atomic():
                for event in ready:
                    self._finish(event, "sent", status, "")
            self.stdout.write(self.style.SUCCESS(f"IndexNow HTTP {status}: {len(ready)} URL(s) accepted (acceptance is not indexing)."))
        elif status in (400, 422):
            for event in ready:
                self._finish(event, "failed", status, reason)
            self.stdout.write(self.style.ERROR(f"IndexNow rejected the batch ({reason}); events marked failed."))
        elif status == 403:
            for event in ready:
                event.last_status, event.last_error = status, "key rejected (403); run aborted"
                event.save(update_fields=["last_status", "last_error", "updated"])
            raise CommandError("IndexNow answered 403: key/keyLocation not accepted. Events kept pending.")
        else:
            delay = int(retry_after) if (retry_after or "").isdigit() else None
            for event in ready:
                self._retry(event, options["max_attempts"], status, reason, delay)
            self.stdout.write(self.style.WARNING(f"IndexNow {reason}; {len(ready)} event(s) scheduled for retry."))

    @staticmethod
    def _finish(event, state, status, error):
        event.state = state
        event.last_status = status
        event.last_error = error
        event.attempts += 1
        if state == "sent":
            event.sent_at = timezone.now()
        event.save()

    @staticmethod
    def _retry(event, max_attempts, status, error, delay=None):
        event.attempts += 1
        event.last_status = status
        event.last_error = str(error)[:300]
        if event.attempts >= max_attempts:
            event.state = "failed"
        else:
            backoff = delay if delay is not None else 60 * (2 ** (event.attempts - 1))
            event.next_attempt = timezone.now() + timedelta(seconds=min(backoff, 86400))
        event.save()
