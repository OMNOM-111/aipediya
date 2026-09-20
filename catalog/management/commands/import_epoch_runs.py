"""Import reproducible Epoch AI runs while retaining unmatched rows for review."""
import csv
import hashlib
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Benchmark, Evaluation, ModelVersion, PublicationRevision, ResearchRecord, ResearchRevision, Source


RUNS = {
    "gpqa_diamond.csv": ("GPQA Diamond", "GPQA Diamond; Epoch AI own run; best score across scorers"),
    "otis_mock_aime_2024_2025.csv": ("Mock AIME 2024/2025", "Mock AIME 2024/2025; Epoch AI own run; best score across scorers"),
    "frontiermath.csv": ("FrontierMath", "FrontierMath; Epoch AI own run; best score across scorers"),
    "swe_bench_verified.csv": ("SWE-bench Verified", "SWE-bench Verified; Epoch AI own run; best score across scorers"),
}
SOURCE_URL = "https://epoch.ai/benchmarks"
SCORE = "Best score (across scorers)"


def model_key(value):
    """Compare a version exactly after separating Epoch's explicit run mode."""
    text = (value or "").casefold().strip()
    text = re.sub(r"_(?:low|medium|high|xhigh|max)$", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


class Command(BaseCommand):
    help = "Publish licensed Epoch AI own-run observations only; external CSVs are never read."

    def add_arguments(self, parser):
        parser.add_argument("directory", help="Directory containing the verified Epoch CSV snapshot.")
        parser.add_argument("--dry-run", action="store_true", help="Validate and report mappings without writing data.")
        parser.add_argument("--checked", default=date.today().isoformat(), help="ISO date on which the source snapshot was reviewed.")

    def handle(self, *args, **options):
        root = Path(options["directory"])
        try:
            checked = date.fromisoformat(options["checked"])
        except ValueError as exc:
            raise CommandError("--checked must be an ISO date") from exc
        observations = self._read(root)
        public_models = list(ModelVersion.objects.filter(published=True, category="text").order_by("pk"))
        by_key = {}
        for model in public_models:
            by_key.setdefault(model_key(model.version), []).append(model)
            by_key.setdefault(model_key(model.name), []).append(model)
        prepared = []
        for observation in observations:
            candidates = {item.pk: item for item in by_key.get(model_key(observation["model_version"]), [])}
            observation["catalog_model_ids"] = sorted(candidates)
            observation["mapping"] = "exact_version" if len(candidates) == 1 else (
                "ambiguous_version" if candidates else "no_exact_published_version"
            )
            prepared.append(observation)
        duplicate_targets = {}
        for item in prepared:
            if item["mapping"] == "exact_version":
                duplicate_targets.setdefault((item["catalog_model_ids"][0], item["benchmark"]), []).append(item)
        for items in duplicate_targets.values():
            if len(items) > 1:
                for item in items:
                    item["mapping"] = "multiple_epoch_modes_for_model_and_benchmark"
        result = {
            "input_observations": len(prepared),
            "mapped_exact": sum(item["mapping"] == "exact_version" for item in prepared),
            "review_required": sum(item["mapping"] != "exact_version" for item in prepared),
            "external_csvs_read": 0, "prices_touched": 0, "dry_run": options["dry_run"],
        }
        if options["dry_run"]:
            self.stdout.write(json.dumps(result, sort_keys=True))
            return
        source, _ = Source.objects.get_or_create(
            url=SOURCE_URL,
            defaults={"title": "Epoch AI - Capabilities & Benchmarking", "publisher": "Epoch AI"},
        )
        created = unchanged = staged = published = revisions = 0
        with transaction.atomic():
            for item in prepared:
                external_id = "epoch-own-run:" + item["source_file"] + ":" + item["source_id"]
                payload_item = {**item, "score": str(item["score"]),
                                "measured": item["measured"].isoformat() if item["measured"] else None}
                payload = {"source": "Epoch AI own run", "license": "CC BY 4.0 attribution", "observation": payload_item}
                record, added = ResearchRecord.objects.get_or_create(
                    external_id=external_id,
                    defaults={"source_record_id": external_id[-80:], "batch": "Epoch AI own runs 2026-09-20", "payload": payload,
                              "state": "review_required", "review_reason": item["mapping"]},
                )
                if not added and record.payload != payload:
                    raise CommandError("Epoch source snapshot changed for an existing observation; stage a new reviewed batch.")
                if added:
                    ResearchRevision.objects.create(record=record, batch=record.batch, action="epoch_stage_create", before={}, after=payload)
                    created += 1
                if item["mapping"] != "exact_version":
                    staged += 1
                    continue
                model = ModelVersion.objects.get(pk=item["catalog_model_ids"][0])
                benchmark, _ = Benchmark.objects.get_or_create(
                    name=item["benchmark"], protocol=item["protocol"],
                    defaults={"category": "text", "unit": "%", "higher_is_better": True},
                )
                conditions = {"ru": f"Собственный запуск Epoch AI; исходная версия: {item['model_version']}; файл: {item['source_file']}; строка: {item['source_id']}.",
                              "en": f"Epoch AI own run; source version: {item['model_version']}; file: {item['source_file']}; row: {item['source_id']}."}
                defaults = {"score": item["score"], "evaluator": "Epoch AI", "independent": True, "public": True,
                            "measured": item["measured"], "conditions": conditions, "source": source, "checked": checked}
                evaluation, evaluation_added = Evaluation.objects.get_or_create(model=model, benchmark=benchmark, defaults=defaults)
                if not evaluation_added:
                    if any(getattr(evaluation, key) != value for key, value in defaults.items()):
                        raise CommandError("Existing Epoch evaluation differs; use an explicit reviewed revision instead of overwriting it.")
                    unchanged += 1
                else:
                    PublicationRevision.objects.create(entity_id=model.research_entity_id or f"model:{model.pk}", model=model,
                        action="publish_evaluation", source_record_ids=[external_id], before={}, after={"benchmark": benchmark.protocol, "score": str(item["score"]), "source": SOURCE_URL})
                    published += 1
                    revisions += 1
                record.state = "accepted"
                record.review_reason = "published: exact model version and licensed Epoch AI own run"
                record.save(update_fields=["state", "review_reason"])
        result.update(created=created, staged=staged, published=published, unchanged=unchanged, revisions=revisions)
        self.stdout.write(json.dumps(result, sort_keys=True))

    def _read(self, root):
        if not root.is_dir():
            raise CommandError("Epoch input directory does not exist")
        rows = []
        for filename, (benchmark, protocol) in RUNS.items():
            path = root / filename
            if not path.is_file():
                raise CommandError(f"Missing required Epoch own-run file: {filename}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    try:
                        score = Decimal(row[SCORE]) * Decimal("100")
                    except (KeyError, InvalidOperation, TypeError) as exc:
                        raise CommandError(f"Invalid {SCORE} in {filename}") from exc
                    if not (Decimal("0") <= score <= Decimal("100")):
                        raise CommandError(f"Out-of-range score in {filename}")
                    started = (row.get("Started at") or "")[:10]
                    try:
                        measured = date.fromisoformat(started) if started else None
                    except ValueError as exc:
                        raise CommandError(f"Invalid Started at in {filename}") from exc
                    if not row.get("id") or not row.get("Model version"):
                        raise CommandError(f"Missing source identity in {filename}")
                    rows.append({"benchmark": benchmark, "protocol": protocol, "source_file": filename, "source_sha256": digest,
                                 "source_id": row["id"], "model_version": row["Model version"], "score": score, "measured": measured})
        return rows
