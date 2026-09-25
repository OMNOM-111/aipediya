"""Apply the Stage-2 final_decisions.json to the Local catalog in one pass.

PUBLIC_VERIFIED -> keep published; set exact `released` OR `approx_released`+
precision (+approx_evidence); set `release_stage`.
NOT_READY       -> published=False (research/evidence/history preserved), number released.
Then clear all model numbers and assign fresh permanent numbers 1..N to the
surviving published models (deterministic by name, then slug) and freeze.

Refuses to run unless EVERY published model has a decision. Dry-run by default.
Never touches Tools numbering or Production.
"""
import json
from datetime import date
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import ModelVersion, PublicationRevision
from catalog.comparison import alphabet

DECISIONS = Path("artifacts/audit-stage2/final_decisions.json")


def parse_approx(s):
    parts = str(s).split("-")
    y = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 1
    d = int(parts[2]) if len(parts) > 2 else 1
    return date(y, m, d)


class Command(BaseCommand):
    help = "Reconcile the Local Models catalog from final_decisions.json."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run).")

    def handle(self, apply=False, **opts):
        decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
        models = list(ModelVersion.objects.filter(entry_type="model"))
        published = [m for m in models if m.published]
        missing = [m.slug for m in published if m.slug not in decisions]
        if missing:
            raise CommandError("%d published models have no decision yet; research incomplete: %s"
                               % (len(missing), missing[:10]))

        stats = {"public_exact": 0, "public_approx": 0, "unpublished": 0, "stage": {}}
        with transaction.atomic():
            for m in models:
                dec = decisions.get(m.slug)
                if not dec:
                    continue
                if dec["verdict"] == "PUBLIC_VERIFIED":
                    stage = dec.get("release_stage") or ""
                    if stage in ("unknown", "released"):
                        stage = "" if stage == "unknown" else "released"
                    fields = {"published": True, "release_stage": stage}
                    if dec.get("exact_release_date"):
                        fields.update(released=parse_approx(dec["exact_release_date"]),
                                      approx_released=None, approx_precision="")
                        stats["public_exact"] += 1
                    elif dec.get("approx_date"):
                        prec = dec.get("approx_precision") or "month"
                        fields.update(released=None, approx_released=parse_approx(dec["approx_date"]),
                                      approx_precision=prec,
                                      approx_evidence={"source_url": dec.get("primary_source_url", ""),
                                                       "date_kind": dec.get("date_kind", ""),
                                                       "evidence": dec.get("evidence_fact", ""),
                                                       "checked": dec.get("verified_at", "")})
                        stats["public_approx"] += 1
                    stats["stage"][stage or "released"] = stats["stage"].get(stage or "released", 0) + 1
                    if apply:
                        ModelVersion.objects.filter(pk=m.pk).update(**fields)
                else:
                    stats["unpublished"] += 1
                    if apply:
                        before = {"published": m.published, "public_number": m.public_number}
                        ModelVersion.objects.filter(pk=m.pk).update(published=False, public_number=None)
                        PublicationRevision.objects.create(
                            model=m, entity_id=m.research_entity_id or m.slug,
                            action="unpublish_not_ready", before=before,
                            after={"reason": dec.get("not_ready_reason", ""),
                                   "evidence": dec.get("evidence_fact", "")})

            # Fresh permanent numbering for the surviving public models.
            survivors = list(ModelVersion.objects.filter(entry_type="model", published=True)) if apply \
                else [m for m in published if decisions.get(m.slug, {}).get("verdict") == "PUBLIC_VERIFIED"]
            survivors.sort(key=lambda o: (alphabet(o.name), o.slug))
            if apply:
                ModelVersion.objects.filter(entry_type="model").update(public_number=None)
                for i, o in enumerate(survivors, 1):
                    ModelVersion.objects.filter(pk=o.pk).update(public_number=i)
            stats["numbered"] = len(survivors)
            if not apply:
                transaction.set_rollback(True)

        self.stdout.write(json.dumps({"apply": apply, **stats}, ensure_ascii=False))
