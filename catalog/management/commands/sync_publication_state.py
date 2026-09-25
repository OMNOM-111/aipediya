"""Carry the owner-approved Local publication state to another database.

``export`` (Local) writes which Models/Tools are public and their permanent
numbers to a JSON manifest that ships with the release code. ``apply`` (the
target, e.g. Production after ``migrate``) brings ``published`` in line with that
manifest through ``save()`` with a publication-revision entry per change, so no
row is deleted and history is kept. It never renumbers: every permanent number
in the target must already equal the manifest, otherwise nothing is written.
Dry-run by default; pass ``--apply`` to write. Tools/models absent from the
manifest, or manifest slugs absent from the target, also abort.
"""
import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import ModelVersion, PublicationRevision, Tool, ToolPublicationRevision
from catalog.translation_pipeline import suppress_auto_translation

SCHEMA = "aipedia-publication-state/1"
ACTION = "sync_release_state"


def current_state():
    return {
        "models": {m.slug: {"published": m.published, "public_number": m.public_number}
                   for m in ModelVersion.objects.filter(entry_type="model").order_by("slug")},
        "tools": {t.slug: {"published": t.published, "public_number": t.public_number}
                  for t in Tool.objects.order_by("slug")},
    }


def plan(manifest, state):
    """Return (changes, problems) for bringing ``state`` to ``manifest``."""
    changes, problems = {"models": [], "tools": []}, []
    for kind in ("models", "tools"):
        want, have = manifest[kind], state[kind]
        for slug in sorted(set(want) ^ set(have)):
            problems.append("%s %s: %s" % (kind, slug, "missing in target" if slug in want else "absent from manifest"))
        for slug in sorted(set(want) & set(have)):
            if want[slug]["public_number"] != have[slug]["public_number"]:
                problems.append("%s %s: number %s in target, %s in manifest"
                                % (kind, slug, have[slug]["public_number"], want[slug]["public_number"]))
            elif want[slug]["published"] != have[slug]["published"]:
                changes[kind].append(slug)
    return changes, problems


def counts(state):
    return {kind: sum(1 for row in state[kind].values() if row["published"]) for kind in ("models", "tools")}


class Command(BaseCommand):
    help = "Export or apply the approved Local publication state (published flags + permanent numbers)."

    def add_arguments(self, parser):
        parser.add_argument("mode", choices=["export", "apply"])
        parser.add_argument("manifest", help="Path of the JSON manifest.")
        parser.add_argument("--release", default="", help="Release name recorded in the manifest (export).")
        parser.add_argument("--apply", action="store_true", help="Write changes (apply mode; default dry-run).")

    def handle(self, mode, manifest, release="", apply=False, **opts):
        path = Path(manifest)
        if mode == "export":
            state = current_state()
            payload = {"schema": SCHEMA, "release": release, "public": counts(state), **state}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            self.stdout.write("exported %s public=%s sha256=%s" % (
                path, payload["public"], hashlib.sha256(path.read_bytes()).hexdigest()))
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA:
            raise CommandError("Unknown manifest schema: %r" % data.get("schema"))
        with transaction.atomic(), suppress_auto_translation():
            changes, problems = plan(data, current_state())
            if problems:
                raise CommandError("%d mismatches, nothing written: %s" % (len(problems), problems[:10]))
            if apply:
                for slug in changes["models"]:
                    obj = ModelVersion.objects.get(slug=slug, entry_type="model")
                    self._flip(obj, data["models"][slug]["published"], data.get("release", ""),
                               lambda before, after: PublicationRevision.objects.create(
                                   model=obj, entity_id=obj.research_entity_id or obj.slug,
                                   action=ACTION, before=before, after=after))
                for slug in changes["tools"]:
                    obj = Tool.objects.get(slug=slug)
                    self._flip(obj, data["tools"][slug]["published"], data.get("release", ""),
                               lambda before, after: ToolPublicationRevision.objects.create(
                                   tool=obj, action=ACTION, before=before, after=after))
                result = counts(current_state())
                if result != data["public"]:
                    raise CommandError("Public counts %s differ from manifest %s; rolled back" % (result, data["public"]))
        self.stdout.write("apply=%s | models changed=%d | tools changed=%d | public now=%s | manifest public=%s" % (
            apply, len(changes["models"]), len(changes["tools"]),
            counts(current_state()), data["public"]))

    @staticmethod
    def _flip(obj, published, release, log):
        before = {"published": obj.published, "public_number": obj.public_number}
        obj.published = published
        obj.save(update_fields=["published"])
        log(before, {"published": published, "public_number": obj.public_number,
                     "reason": "approved Local release state", "release": release})
