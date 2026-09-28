"""Independent-evaluation audit of the master (2026-09-27): evidence base for a future AIpediya Rating.

Owner task 2026-09-27 (Timeline card EVAL-EVIDENCE-AUDIT-2026-09-27). Scope is the
master only: Evaluations, Facts (``independent_evaluation_status``) and Changelog.
Names, Record IDs, numbers, dates, prices, Offers/Access/Origins, Local SQLite and
Production are not touched.

Sources (pinned snapshots under artifacts/eval-audit-2026-09-27 and
artifacts/epoch-ai-2026-09-27/data; see the audit report for licences):

* Epoch AI benchmarking hub, snapshot 2026-09-27: own runs (CC BY 4.0, Public=YES)
  and ``*_external.csv`` rows, which "retain their original licensing" (Epoch
  use-this-data page). External rows are Public=YES only where the original
  source licence is open (ForecastBench CC BY-SA 4.0, Surface Evolver Apache-2.0,
  AlgoTune MIT); otherwise Public=NO. Epoch copies of Aider and WebDev Arena are
  skipped because the primary sources below are imported directly.
* lmarena-ai/leaderboard-dataset (CC BY 4.0), ``latest`` split, category overall.
* Aider leaderboards YAML (Apache-2.0, repository data).
* Hugging Face Open ASR Leaderboard result CSVs (no licence stated: Public=NO).
* MTEB results repository (CC0-1.0): task files added by contributors other than
  the model developer's release submission.

Only exact versions from tools/eval_audit_2026_09_27_map.py are attached. Every
row keeps the source score and unit in ``Conditions Extra (JSON)`` together with
rating-eligibility flags; percentages are derived only from bounded 0–1 values.
Each master model receives an evidenced ``independent_evaluation_status`` fact.
Re-running adds nothing new (rows keyed by the source observation).

  .venv\\Scripts\\python.exe tools\\master_eval_audit_2026_09_27.py --book AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx [--dry-run]
"""
import argparse
import collections
import csv
import glob
import hashlib
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402
from eval_audit_2026_09_27_map import CONFIGURATION_OF, NEEDS_REVIEW, NOT_EXACT, PUBLISHED  # noqa: E402

MAP = {**PUBLISHED, **NEEDS_REVIEW}

RUN = "eval-audit-2026-09-27"
CHECKED = "2026-09-27"
EPOCH = ROOT / "artifacts/epoch-ai-2026-09-27/data"
EPOCH_SNAPSHOT = "Epoch AI benchmarking hub snapshot 2026-09-27"
AUDIT = ROOT / "artifacts/eval-audit-2026-09-27"
ARENA_REV = "a4e245e5a4cbea662032d4c4b8460dfd4432be3e"
ARENA_URL = "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/%s" % ARENA_REV
ASR_URL = "https://huggingface.co/spaces/hf-audio/open_asr_leaderboard"

# --------------------------------------------------------------------- Epoch
OWN_FILES = {  # file -> benchmark name used by the existing master rows
    "gpqa_diamond.csv": "GPQA Diamond", "otis_mock_aime_2024_2025.csv": "Mock AIME 2024/2025",
    "frontiermath.csv": "FrontierMath", "frontiermath_tier_4.csv": "FrontierMath-Tier-4-2025-07-01-Private",
    "frontiermath_tiers_1_3_v2.csv": "FrontierMath-Tiers-1-3-v2-Private", "frontiermath_tier_4_v2.csv": "FrontierMath-Tier-4-v2-Private",
    "frontiermath_erdos.csv": "FrontierMath Open Problems (Erdős)", "swe_bench_verified.csv": "SWE-bench Verified",
    "math_level_5.csv": "MATH level 5", "simpleqa_verified.csv": "SimpleQA Verified", "chess_puzzles.csv": "Chess Puzzles",
    "ebr_bench.csv": "EBR-bench", "mystery_game_puzzles.csv": "Mystery Game Puzzles", "mirrorcode.csv": "MirrorCode",
    "furniture_assembly.csv": "Furniture Assembly",
}
OWN_CATEGORY = {"furniture_assembly.csv": "image"}

# External files. kind: fraction (0–1 -> %), percent (0–100 %), bounded (other bounded scale),
# unbounded. public: original-source licence allows republication.
# evaluator_dev: organizations that are themselves model developers (conflict flag / developer rows).
EXT = {
    "adversarial_nli_external.csv": dict(bench="ANLI", col="Score", kind="fraction", papers=True),
    "arc_ai2_external.csv": dict(bench="ARC (AI2) Challenge", col="Challenge score", kind="fraction", papers=True),
    "bbh_external.csv": dict(bench="BIG-Bench Hard", col="Average", kind="fraction", papers=True),
    "bool_q_external.csv": dict(bench="BoolQ", col="Score", kind="fraction", papers=True),
    "common_sense_qa_2_external.csv": dict(bench="CommonsenseQA 2.0", col="Score", kind="fraction", papers=True),
    "gsm8k_external.csv": dict(bench="GSM8K", col="EM", kind="fraction", papers=True),
    "hella_swag_external.csv": dict(bench="HellaSwag", col="Overall accuracy", kind="fraction", papers=True),
    "lambada_external.csv": dict(bench="LAMBADA", col="Score", kind="fraction", papers=True),
    "mmlu_external.csv": dict(bench="MMLU", col="EM", kind="fraction", papers=True),
    "open_book_qa_external.csv": dict(bench="OpenBookQA", col="Accuracy", kind="fraction", papers=True),
    "piqa_external.csv": dict(bench="PIQA", col="Score", kind="fraction", papers=True),
    "trivia_qa_external.csv": dict(bench="TriviaQA", col="EM", kind="fraction", papers=True),
    "wino_grande_external.csv": dict(bench="WinoGrande", col="Accuracy", kind="fraction", papers=True),
    "superglue_external.csv": dict(bench="SuperGLUE", col="Score", kind="fraction", papers=True),
    "cybench_external.csv": dict(bench="Cybench (unguided)", col="Unguided % Solved", kind="fraction", papers=True,
                                 evaluator="Cybench (Stanford)", url="https://cybench.github.io/"),
    "arc_agi_external.csv": dict(bench="ARC-AGI-1", col="Score", kind="fraction", evaluator="ARC Prize Foundation",
                                 url="https://arcprize.org/leaderboard", licence="arcprize.org terms: no reproduction without written permission"),
    "arc_agi_2_external.csv": dict(bench="ARC-AGI-2", col="Score", kind="fraction", evaluator="ARC Prize Foundation",
                                   url="https://arcprize.org/leaderboard", licence="arcprize.org terms: no reproduction without written permission"),
    "ale_bench_external.csv": dict(bench="ALE-Bench", col="Performance", kind="unbounded", unit="points", evaluator="Sakana AI",
                                   url="https://sakanaai.github.io/ALE-Bench-Leaderboard/", dev=("sakana",), licence="no licence stated for leaderboard results"),
    "algotune_external.csv": dict(bench="AlgoTune", col="Score", kind="unbounded", unit="× speedup", evaluator="AlgoTune (Press et al.)",
                                  url="https://algotune.io/", public=True, licence="MIT (github.com/oripress/AlgoTune, results/ in repository)"),
    "apex_agents_external.csv": dict(bench="APEX-Agents", col="Pass@1 score", kind="fraction", evaluator="Mercor",
                                     url="https://www.mercor.com/apex/", licence="tasks CC BY; leaderboard results licence not stated"),
    "balrog_external.csv": dict(bench="BALROG", col="Average progress", kind="fraction", evaluator="BALROG (UCL DARK)",
                                url="https://balrogai.com/", licence="code MIT; leaderboard results not in repository, no licence"),
    "blueprint_bench_2_external.csv": dict(bench="Blueprint-Bench 2", col="Score", kind="fraction", evaluator="Andon Labs",
                                           url="https://andonlabs.com/evals/blueprint-bench-2", category="image"),
    "btf3_external.csv": dict(bench="Bench to the Future 3", col="Pooled score", kind="unbounded", unit="pooled Brier/RPS", higher=False,
                              evaluator="FutureSearch", url="https://evals.futuresearch.ai/#btf3"),
    "cad_eval_external.csv": dict(bench="CadEval", col="Overall pass (%)", kind="fraction", evaluator="CadEval (Will Patrick)", url="https://willpatrick.xyz/cadevalresults"),
    "cl_bench_external.csv": dict(bench="CL-bench", col="Overall", kind="fraction", evaluator="Tencent Hunyuan & Fudan NLP", url="https://www.clbench.com/", dev=("tencent",)),
    "cl_bench_life_external.csv": dict(bench="CL-bench Life", col="Overall", kind="fraction", evaluator="Tencent Hunyuan & Fudan NLP", url="https://www.clbench.com/", dev=("tencent",)),
    "critpt_external.csv": dict(bench="CritPt", col="Accuracy", kind="fraction", evaluator="Artificial Analysis",
                                url="https://artificialanalysis.ai/evaluations/critpt", licence="Artificial Analysis terms block republication"),
    "cursorbench_external.csv": dict(bench="CursorBench", col="Score", kind="fraction", evaluator="Cursor (Anysphere)", url="https://cursor.com/cursorbench", dev=("cursor", "anysphere")),
    "deepresearchbench_external.csv": dict(bench="DeepResearch Bench", col="Average score", kind="fraction", evaluator="FutureSearch", url="https://evals.futuresearch.ai/#drb"),
    "deepswe_external.csv": dict(bench="DeepSWE", col="Pass@1", kind="fraction", evaluator="Datacurve", url="https://deepswe.datacurve.ai/"),
    "dtbench_external.csv": dict(bench="DTBench", col="Accuracy", kind="fraction", evaluator="Conceptual Reasoning Index (Redwood Research, with Anthropic)",
                                 url="https://conceptualreasoning.ai/dtbench", dev=("anthropic",)),
    "lmca_external.csv": dict(bench="LMCA", col="Score", kind="percent", evaluator="Conceptual Reasoning Index (Redwood Research, with Anthropic)",
                              url="https://conceptualreasoning.ai/lmca", dev=("anthropic",)),
    "enigma_eval_external.csv": dict(bench="EnigmaEval", col="Accuracy", kind="fraction", evaluator="Scale AI", url="https://labs.scale.com/leaderboard/enigma_eval", se="Accuracy Standard Error"),
    "exploitbench_external.csv": dict(bench="ExploitBench", col="Mean capability", kind="fraction", evaluator="ExploitBench (CMU)", url="https://exploitbench.ai/"),
    "fictionlivebench_external.csv": dict(bench="Fiction.LiveBench (16k)", col="16k token score", kind="fraction", evaluator="Fiction.live", url="https://fiction.live/stories/Fiction-liveBench"),
    "forecastbench_external.csv": dict(bench="ForecastBench (Brier Index)", col="Overall score", kind="percent", evaluator="Forecasting Research Institute (ForecastBench)",
                                       url="https://www.forecastbench.org/leaderboards/", public=True, licence="CC BY-SA 4.0 (forecastbench.org; github.com/forecastingresearch/forecastbench-datasets)",
                                       ci=("Overall 95% CI low", "Overall 95% CI high")),
    "frontiercode_external.csv": dict(bench="FrontierCode", col="Main score", kind="fraction", evaluator="Cognition", url="https://cognition.com/frontiercode", dev=("cognition",)),
    "frontierswe_external.csv": dict(bench="FrontierSWE", col="Score", kind="fraction", evaluator="FrontierSWE", url="https://www.frontierswe.com/"),
    "gbaeval_external.csv": dict(bench="GBAEval", col="Overall score", kind="fraction", evaluator="GBAEval", url="https://gbaeval.com/"),
    "gdp_pdf_external.csv": dict(bench="GDP.pdf", col="GDP.pdf score", kind="fraction", evaluator="Surge AI", url="https://surgehq.ai/benchmarks/gdp-pdf"),
    "gdpval_external.csv": dict(bench="GDPval (win rate)", col="Win Rate (%)", kind="fraction", evaluator="OpenAI", url="https://evals.openai.com/gdpval/leaderboard", dev=("openai",)),
    "geobench_external.csv": dict(bench="GeoBench", col="ACW Country %", kind="fraction", evaluator="GeoBench", url="https://geobench.org/", category="image"),
    "gso_external.csv": dict(bench="GSO", col="Score OPT@1", kind="fraction", evaluator="GSO (Shetty et al.)", url="https://gso-bench.github.io/"),
    "hle_external.csv": dict(bench="Humanity's Last Exam", col="Accuracy", kind="fraction", evaluator="Scale AI & Center for AI Safety",
                             url="https://scale.com/leaderboard/humanitys_last_exam", se="Accuracy Standard Error"),
    "lech_mazur_writing_external.csv": dict(bench="Lech Mazur Creative Writing", col="Mean score", kind="bounded", bounded=(0, 10), unit="/10",
                                            evaluator="Lech Mazur", url="https://github.com/lechmazur/writing"),
    "live_bench_external.csv": dict(bench="LiveBench", col="Global average", kind="percent", evaluator="LiveBench", url="https://livebench.ai/",
                                    licence="LiveBench terms block republication (prior master decision)"),
    "metr_time_horizons_external.csv": dict(bench="METR 50% time horizon", col="Time horizon", kind="unbounded", unit="min", evaluator="METR",
                                            url="https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/", ci=("CI_low", "CI_high"),
                                            licence="github.com/METR/eval-analysis-public has no licence file"),
    "mindcube_external.csv": dict(bench="MindCube", col="Overall score", kind="fraction", evaluator="MindCube authors", url="https://mind-cube.github.io/", category="image"),
    "osworld_2_external.csv": dict(bench="OSWorld 2.0", col="Binary accuracy", kind="fraction", evaluator="XLANG Lab (OSWorld)", url="https://osworld-v2.xlang.ai/", category="image"),
    "posttrainbench_external.csv": dict(bench="PostTrainBench", col="Average (%)", kind="fraction", evaluator="PostTrainBench (Tübingen AI Safety & Alignment group)", url="https://github.com/aisa-group/PostTrainBench"),
    "proofbench_external.csv": dict(bench="ProofBench", col="Accuracy", kind="fraction", evaluator="Vals AI", url="https://www.vals.ai/benchmarks/proof_bench", se="Accuracy Standard Error"),
    "rli_external.csv": dict(bench="Remote Labor Index", col="Score", kind="fraction", evaluator="Scale AI & Center for AI Safety", url="https://labs.scale.com/leaderboard/rli"),
    "scicode_external.csv": dict(bench="SciCode", col="Score", kind="fraction", evaluator="Artificial Analysis",
                                url="https://artificialanalysis.ai/evaluations/scicode", licence="Artificial Analysis terms block republication"),
    "simplebench_external.csv": dict(bench="SimpleBench", col="Score (AVG@5)", kind="fraction", evaluator="SimpleBench", url="https://simple-bench.com/",
                                     licence="dataset/code MIT; leaderboard results no licence"),
    "spatialviz_bench_external.csv": dict(bench="SpatialViz-Bench", col="Overall score", kind="fraction", evaluator="SpatialViz-Bench authors", url="https://arxiv.org/abs/2507.07610", category="image"),
    "surface_evolver_bench_external.csv": dict(bench="Surface Evolver Bench", col="Mean score", kind="fraction", evaluator="Surface Evolver LLM eval (yhenon)",
                                               url="https://yhenon.github.io/surface-evolver-llm-eval/", public=True,
                                               licence="Apache-2.0 (github.com/yhenon/surface-evolver-llm-eval, docs/data in repository)"),
    "terminalbench_external.csv": dict(bench="Terminal-Bench 2.0", col="Accuracy mean", kind="fraction", evaluator="Terminal-Bench (Stanford & Laude Institute)",
                                       url="https://www.tbench.ai/leaderboard/terminal-bench/2.0", se="Accuracy SE", agent_org="Agent Org",
                                       licence="github.com/laude-institute/terminal-bench-leaderboard has no licence"),
    "the_agent_company_external.csv": dict(bench="TheAgentCompany", col="% Resolved", alt_col="% Score", kind="fraction", evaluator="TheAgentCompany (CMU)",
                                           url="https://the-agent-company.com/", licence="experiments repository has no licence"),
    "vending_bench_2_external.csv": dict(bench="Vending-Bench 2", col="Score", kind="unbounded", unit="USD", evaluator="Andon Labs", url="https://andonlabs.com/evals/vending-bench-2"),
    "vpct_external.csv": dict(bench="VPCT", col="Correct", kind="fraction", evaluator="VPCT (Chase Brower)", url="https://cbrower.dev/vpct", category="image"),
    "weirdml_external.csv": dict(bench="WeirdML", col="Accuracy", kind="fraction", evaluator="WeirdML (Håvard Tveit Ihle)", url="https://htihle.github.io/weirdml.html"),
}
SKIP_FILES = {  # file -> reason
    "aider_polyglot_external.csv": "Epoch copy; the primary Aider leaderboard (Apache-2.0) is imported directly",
    "webdev_arena_external.csv": "Epoch copy; the primary lmarena-ai/leaderboard-dataset webdev subset (CC BY 4.0) is imported directly",
    "os_world_external.csv": "leaderboard mixes self-reported submissions without submitter attribution; runner not identifiable",
    "video_mme_external.csv": "leaderboard compiled from model papers (self-reported); runner not identifiable",
    "science_qa_external.csv": "leaderboard compiled from model papers (self-reported); runner not identifiable",
}
# Paper/report title fragment -> publishing organization (lower-case key used for developer matching).
PAPERS = {
    "llama 2: open foundation": ("Meta AI", "meta"), "llama: open and efficient": ("Meta AI", "meta"),
    "the llama 3 herd": ("Meta AI", "meta"), "qwen technical report": ("Alibaba Qwen", "alibaba"),
    "qwen2.5-coder technical report": ("Alibaba Qwen", "alibaba"), "falcon series": ("Technology Innovation Institute", "tii"),
    "falcon2-11b": ("Technology Innovation Institute", "tii"), "mixtral of experts": ("Mistral AI", "mistral"),
    "gemma: open models": ("Google DeepMind", "google"), "nemotron-4 15b": ("NVIDIA", "nvidia"),
    "phi-3 technical report": ("Microsoft", "microsoft"), "phi-1.5 technical report": ("Microsoft", "microsoft"),
    "baichuan 2": ("Baichuan", "baichuan"), "yi: open foundation": ("01.AI", "01.ai"), "gpt-4 technical report": ("OpenAI", "openai"),
    "model card and evaluations for claude": ("Anthropic", "anthropic"), "claude 3 model family": ("Anthropic", "anthropic"),
    "megatron-turing nlg": ("Microsoft & NVIDIA", "microsoft"), "glam: efficient scaling": ("Google", "google"),
    "scaling language models: methods": ("DeepMind", "google"), "training compute-optimal": ("DeepMind", "google"),
    "language models are few-shot": ("OpenAI", "openai"), "exploring the limits of transfer": ("Google", "google"),
    "switch transformers": ("Google", "google"), "palm 2 technical report": ("Google", "google"),
    "palm: scaling language modeling": ("Google", "google"), "phi-4 technical report": ("Microsoft", "microsoft"), "xgen-7b": ("Salesforce", "salesforce"), "deepseek-v3 technical report": ("DeepSeek", "deepseek"),
    "unicorn on rainbow": ("Allen Institute for AI", "ai2"), "adversarial nli": ("UNC & Facebook AI", "meta"),
    "commonsenseqa 2.0": ("Allen Institute for AI", "ai2"), "decker": ("academic paper", "academic"),
    "system card": ("model developer system card", "self"), "model card": ("model developer model card", "self"),
    "anthropic annoucement": ("Anthropic", "anthropic"), "stanford helm": ("Stanford CRFM (HELM)", "helm"),
    "stanford crfm": ("Stanford CRFM (HELM)", "helm"), "cybench leaderboard": ("Cybench (Stanford)", "cybench"),
}
HELM_URL = "https://crfm.stanford.edu/helm/"
DEV_KEYS = {  # master Developer -> developer keys (Alphabet units treated as one developer)
    "openai": ("openai",), "anthropic": ("anthropic",), "google": ("google",), "deepmind": ("google",),
    "meta": ("meta",), "mistral": ("mistral",), "alibaba": ("alibaba",), "qwen": ("alibaba",), "deepseek": ("deepseek",),
    "nvidia": ("nvidia",), "microsoft": ("microsoft",), "amazon": ("amazon",), "tencent": ("tencent",), "z.ai": ("zhipu",),
    "zhipu": ("zhipu",), "minimax": ("minimax",), "moonshot": ("moonshot",), "xai": ("xai",), "spacexai": ("xai",),
    "cohere": ("cohere",), "sakana": ("sakana",), "stability": ("stability",), "black forest": ("bfl",), "runway": ("runway",),
    "bytedance": ("bytedance",), "elevenlabs": ("elevenlabs",), "ai21": ("ai21",),
    "technology innovation": ("tii",), "01.ai": ("01.ai",), "baichuan": ("baichuan",), "salesforce": ("salesforce",),
    "allen institute": ("ai2",), "eleutherai": ("eleutherai",), "databricks": ("databricks",), "ibm": ("ibm",),
}
SUFFIX = re.compile(r"^(?P<b>.+?)(?:_(?P<s>high|low|medium|minimal|none|xhigh|max|unknown|thinking|\d+K))?$")

# --------------------------------------------------------------------- Arena
ARENA = {  # subset -> (benchmark name, category)
    "text_style_control": ("LMArena Text (style control)", "text"),
    "vision_style_control": ("LMArena Vision (style control)", "image"),
    "webdev": ("LMArena WebDev / Code Arena", "text"),
    "document": ("LMArena Document Arena", "text"),
    "text_to_image": ("LMArena Text-to-Image", "image"),
    "image_edit": ("LMArena Image Edit", "image"),
    "text_to_video": ("LMArena Text-to-Video", "video"),
    "image_to_video": ("LMArena Image-to-Video", "video"),
    "video_edit": ("LMArena Video Edit", "video"),
}
ARENA_SKIPPED = {"text": "raw (non style-controlled) duplicate of the same battles as text_style_control",
                 "vision": "raw duplicate of vision_style_control", "search": "search-augmented systems, not the bare model"}

# --------------------------------------------------------------------- helpers


def dec(value):
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        return None


def fmt(value, places=3):
    q = value.quantize(Decimal(1).scaleb(-places))
    text = format(q.normalize(), "f")
    return "0" if text in ("-0", "") else text


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dev_keys(developer):
    low = (developer or "").lower()
    keys = set()
    for fragment, values in DEV_KEYS.items():
        if fragment in low:
            keys.update(values)
    return keys


def config_label(suffix):
    if not suffix or suffix == "unknown":
        return "default (effort unspecified by source)"
    if suffix.endswith("K") and suffix[:-1].isdigit():
        return "thinking budget %s" % suffix
    return suffix


def normalize(kind, raw, bounded=None):
    """(score, unit, extra) keeping the source score; % only when mathematically exact."""
    extra = {"source_score": str(raw)}
    if kind == "fraction":
        extra.update(source_unit="fraction (0–1)", bounded_range=[0, 1], normalized_percent=fmt(raw * 100),
                     normalization_method="score × 100 (exact)")
        return raw * 100, "%", extra
    if kind == "percent":
        extra.update(source_unit="percent (0–100)", bounded_range=[0, 100], normalized_percent=fmt(raw),
                     normalization_method="none (source is a percentage)")
        return raw, "%", extra
    if kind == "bounded":
        low, high = bounded
        extra.update(source_unit="points (%s–%s)" % (low, high), bounded_range=[low, high],
                     normalized_percent=fmt((raw - low) / (high - low) * 100), normalization_method="(score − min)/(max − min) × 100 (exact, known scale)")
        return raw, None, extra
    extra.update(source_unit="unbounded", normalized_percent=None, normalization_method="not normalizable (unbounded scale)")
    return raw, None, extra


# --------------------------------------------------------------------- collectors


class Collector:
    def __init__(self, rows, models):
        self.rows = rows
        self.models = models
        # rows written by an earlier pass of this run are recomputed (corrections are logged), never duplicated
        self.run_rows = {r.get("Source Record ID"): r for r in rows["Evaluations"] if RUN in (r.get("Key") or "")}
        self.known_source_ids = {r.get("Source Record ID") for r in rows["Evaluations"]
                                 if r.get("Source Record ID") and RUN not in (r.get("Key") or "")}
        self.out = []
        self.updates = []
        self.skipped = collections.Counter()
        self.seen = set()
        self.values = {}
        self.duplicates = []

    def add(self, rid, **row):
        source_id = row["Source Record ID"]
        if source_id in self.known_source_ids or source_id in self.seen:
            self.skipped["already present / duplicate observation"] += 1
            return
        self.seen.add(source_id)
        # the same value of the same model/benchmark/configuration from the same evaluator and source row label is one
        # observation, even when an aggregator lists it twice (e.g. one paper table copied into two hub rows)
        value_key = (rid, row["Benchmark"], row["Evaluator"], row["Score"], row.get("Configuration"), row.get("Source Model"),
                     (row.get("Conditions Extra (JSON)") or {}).get("source_row_name") if isinstance(row.get("Conditions Extra (JSON)"), dict) else None)
        if value_key in self.values:
            self.skipped["duplicate value of one observation (aggregator repeat)"] += 1
            self.duplicates.append((source_id, self.values[value_key]))
            return
        self.values[value_key] = source_id
        obs = hashlib.sha256(("%s:%s:%s" % (RUN, rid, source_id)).encode()).hexdigest()
        row.update({"Key": "evaluation-%s-%s" % (RUN, obs[:16]), "Record Type": "model", "Record ID": rid,
                    "Checked": CHECKED, "Observation Key": obs})
        if source_id in self.run_rows:
            self.updates.append(row)
        else:
            self.out.append(row)


def epoch_index():
    bases = {}
    for rid, spec in MAP.items():
        for base in spec.get("epoch", []):
            bases[base] = rid
    return bases


def epoch_match(version, bases):
    version = (version or "").strip()
    if version in bases:
        return bases[version], ""
    match = SUFFIX.match(version)
    if match and match.group("s") and match.group("b") in bases:
        return bases[match.group("b")], match.group("s")
    return None, None


def collect_epoch(col, report):
    bases = epoch_index()
    for filename, bench in OWN_FILES.items():
        path = EPOCH / filename
        file_hash = sha(path)
        for row in csv.DictReader(open(path, encoding="utf-8")):
            rid, suffix = epoch_match(row["Model version"], bases)
            if not rid:
                continue
            value = dec(row.get("Best score (across scorers)"))
            if value is None:
                col.skipped["epoch own: empty score"] += 1
                continue
            score, unit, extra = normalize("fraction", value)
            mode = config_label(suffix)
            stderr = dec(row.get("stderr"))
            extra.update(rating_eligible=True, evaluator_type="independent benchmark organization", evaluator_family="Epoch AI",
                         licence="CC BY 4.0 (Epoch AI own evaluation)", exact_version_basis="Epoch model version %s mapped by hand" % row["Model version"].strip(),
                         stderr=str(stderr) if stderr is not None else None, log_viewer=row.get("Log viewer") or None)
            en = ("Epoch AI own run; %s; version: %s; mode: %s; source id: %s; file: %s. CC BY 4.0, Epoch AI. Snapshot 2026-09-27. "
                  "Source column Best score (across scorers), not AIpedia's selection of the best effort." % (bench, row["Model version"].strip(), mode, row["id"], filename))
            ru = ("Собственный прогон Epoch AI; %s; версия: %s; режим: %s; исходный id: %s; файл: %s. CC BY 4.0, Epoch AI. Снимок 2026-09-27. "
                  "Показана колонка источника Best score (across scorers), не выбор лучшего режима AIpedia." % (bench, row["Model version"].strip(), mode, row["id"], filename))
            col.add(rid, **{"Benchmark": bench, "Protocol": "%s; Epoch AI own run; best score across scorers" % bench,
                            "Benchmark Category": OWN_CATEGORY.get(filename, "text"), "Unit": unit, "Higher Is Better": "YES",
                            "Score": fmt(score), "Evaluator": "Epoch AI", "Result Kind": "independent", "Independent": "YES", "Public": "YES",
                            "Measured": (row.get("Started at") or "")[:10], "Configuration": mode,
                            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra,
                            "Source URL": "https://epoch.ai/benchmarks", "Source Model": row["Model version"].strip(),
                            "Source Record ID": "%s:%s" % (filename, row["id"]), "Snapshot": "2026-09-27", "Source SHA256": file_hash})
    for filename in sorted(os.listdir(EPOCH)):
        if not filename.endswith("_external.csv"):
            continue
        if filename in SKIP_FILES:
            report["skipped_files"][filename] = SKIP_FILES[filename]
            continue
        rule = EXT.get(filename)
        if rule is None:
            report["skipped_files"][filename] = "no rule (no mapped catalog model)"
            continue
        path = EPOCH / filename
        file_hash = sha(path)
        for row in csv.DictReader(open(path, encoding="utf-8")):
            rid, suffix = epoch_match(row.get("Model version"), bases)
            if not rid:
                continue
            if not row.get("id"):  # a few files carry no Airtable id: content hash of the source row
                row["id"] = "row-" + hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
            column = rule["col"] if rule["col"] in row else rule.get("alt_col", rule["col"])
            value = dec(row.get(column))
            if value is None:
                col.skipped["epoch external: empty score"] += 1
                continue
            model = col.models[rid]
            devs = dev_keys(model.get("Developer"))
            evaluator, url, public, licence = rule.get("evaluator"), rule.get("url"), rule.get("public", False), rule.get("licence")
            source = (row.get("Source") or "").strip()
            link = (row.get("Source link") or "").strip()
            evaluator_type, independent, eligible, exclusion = "independent leaderboard", True, True, None
            if rule.get("papers") and source and "leaderboard" not in source.lower():
                org, key = next(((o, k) for frag, (o, k) in PAPERS.items() if frag in source.lower()), (None, None))
                if key in ("helm",):
                    evaluator, url, evaluator_type = org, link or HELM_URL, "university lab (HELM)"
                    licence = "HELM code Apache-2.0; aggregated scores carry no stated licence"
                elif key is None:
                    col.skipped["paper source not classified: " + source[:60]] += 1
                    continue
                else:
                    evaluator, url = "%s (%s)" % (org, source[:80]), link or url
                    licence = "paper/report table; no reuse licence for results"
                    if key == "self" or key in devs:
                        independent, evaluator_type = False, "developer technical report"
                    else:
                        evaluator_type, eligible, exclusion = "competitor technical report", False, "baseline measured by a competing model developer"
            elif rule.get("papers") and source:
                org, key = next(((o, k) for frag, (o, k) in PAPERS.items() if frag in source.lower()), (source, "leaderboard"))
                evaluator, url = org if key != "leaderboard" else source, link or url or HELM_URL
                if key == "helm":
                    evaluator_type, licence = "university lab (HELM)", "HELM code Apache-2.0; aggregated scores carry no stated licence"
            elif source and ("system card" in source.lower() or "model card" in source.lower() or "annoucement" in source.lower()):
                independent, evaluator_type, evaluator, url = False, "developer report", source, link or url
            if evaluator is None:
                col.skipped["no evaluator for %s" % filename] += 1
                continue
            if rule.get("dev") and devs & set(rule["dev"]):
                independent, evaluator_type = False, "benchmark run by the model developer"
            elif rule.get("dev"):
                eligible, exclusion = False, "evaluator organization is itself an AI model developer (conflict of interest)"
                evaluator_type = "benchmark by an AI model developer"
            agent_org = (row.get(rule.get("agent_org", "")) or "").strip().lower() if rule.get("agent_org") else ""
            if agent_org and dev_keys(agent_org) & devs:
                independent, evaluator_type = False, "agent harness submitted by the model developer"
            score, unit, extra = normalize(rule["kind"], value, rule.get("bounded"))
            unit = unit or rule.get("unit", "points")
            if not public and not licence:
                licence = "no licence for leaderboard results stated"
            if not public:
                exclusion = exclusion or "not republishable (licence)"
            lo = hi = None
            if rule.get("ci"):
                lo, hi = dec(row.get(rule["ci"][0])), dec(row.get(rule["ci"][1]))
            se = dec(row.get(rule["se"])) if rule.get("se") else None
            if se is not None and rule["kind"] == "fraction" and se <= 1 and value <= 1:
                se_note = str(se)
            else:
                se_note = str(se) if se is not None else None
            harness = (row.get("Harness") or row.get("Agent") or row.get("Scaffold") or "").strip()
            name = (row.get("Name") or "").strip()
            effort = (row.get("Reasoning effort") or row.get("Reasoning level") or "").strip()
            config = config_label(suffix)
            if effort and config.startswith("default"):
                config = effort
            if harness:
                config = "%s; harness %s" % (config, harness)
            extra.update(rating_eligible=bool(independent and eligible and public), rating_exclusion_reason=None if (independent and eligible and public) else
                         (exclusion or ("not independent" if not independent else None)),
                         evaluator_type=evaluator_type, evaluator_family=evaluator, licence=licence or "", source_row_name=name or None,
                         standard_error=se_note, exact_version_basis="Epoch model version %s mapped by hand" % row["Model version"].strip(),
                         retrieved_via=EPOCH_SNAPSHOT + " (external data keeps its original licence)", measured_note=row.get("Notes") or None)
            measured = (row.get("Date of evaluation") or row.get("Run date") or row.get("Started at") or "")[:10]
            kind = "independent" if independent else "developer"
            en = ("%s result for %s (%s); source row '%s' (%s). Retrieved via %s, file %s, row %s; original licence: %s." %
                  (evaluator, rule["bench"], config, name or row["Model version"].strip(), source or url, EPOCH_SNAPSHOT, filename, row["id"], licence or "open"))
            ru = ("Результат %s в %s (%s); строка источника «%s» (%s). Получено через снимок Epoch AI 2026-09-27, файл %s, строка %s; исходная лицензия: %s." %
                  (evaluator, rule["bench"], config, name or row["Model version"].strip(), source or url, filename, row["id"], licence or "открытая"))
            col.add(rid, **{"Benchmark": rule["bench"], "Protocol": "%s; %s; score column %s" % (rule["bench"], evaluator, column),
                            "Benchmark Category": rule.get("category", "text"), "Unit": unit, "Higher Is Better": "NO" if rule.get("higher") is False else "YES",
                            "Score": fmt(score), "Evaluator": evaluator[:120], "Result Kind": kind, "Independent": "YES" if independent else "NO",
                            "Public": "YES" if public else "NO", "Measured": measured, "Configuration": config[:200],
                            "Confidence Low": fmt(lo) if lo is not None else "", "Confidence High": fmt(hi) if hi is not None else "",
                            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra,
                            "Source URL": url or "https://epoch.ai/benchmarks", "Source Model": row["Model version"].strip(),
                            "Source Record ID": "%s:%s" % (filename, row["id"]), "Snapshot": EPOCH_SNAPSHOT, "Source SHA256": file_hash})


def arena_config(name):
    tags = re.findall(r"\(([^)]+)\)|\[([^\]]+)\]", name)
    labels = [a or b for a, b in tags if "nano-banana" not in (a or b)]  # product nicknames, not configurations
    base = re.sub(r"\s*[\(\[].*$", "", name)
    dated = re.search(r"-(xhigh|high|medium|low|max)-\d{8}$", base)
    if dated:
        return "; ".join([dated.group(1)] + labels)
    for suffix in ("-thinking-32k", "-thinking-16k", "-high-32k", "-xhigh", "-high", "-medium", "-max", "-audio-1080p", "-audio", "-1080p", "-720p", "-agent", "-2k"):
        if base.endswith(suffix):
            labels.insert(0, suffix.lstrip("-"))
            break
    return "; ".join(labels) or "default"


def collect_arena(col, report):
    data = json.load(open(AUDIT / "lmarena/overall.json", encoding="utf-8"))
    names = {}
    for rid, spec in MAP.items():
        for name in spec.get("arena", []):
            names[name] = rid
    for subset, payload in data.items():
        if subset not in ARENA:
            report["skipped_files"]["lmarena:" + subset] = ARENA_SKIPPED.get(subset, "not used")
            continue
        bench, category = ARENA[subset]
        for row in payload["rows"]:
            rid = names.get(row["model_name"])
            if not rid:
                continue
            rating = dec(row["rating"])
            config = arena_config(row["model_name"])
            extra = {"source_score": str(row["rating"]), "source_unit": "Arena score (Bradley–Terry, unbounded)", "bounded_range": None,
                     "normalized_percent": None, "normalization_method": "not normalizable (relative preference scale)",
                     "rating_eligible": True, "rating_exclusion_reason": None, "evaluator_type": "independent leaderboard (human pairwise preference)",
                     "evaluator_family": "LMArena", "licence": "CC BY 4.0 (lmarena-ai/leaderboard-dataset)", "vote_count": row.get("vote_count"),
                     "rank": row.get("rank"), "variance": row.get("variance"), "comparability": "compare only within the same arena and publish date",
                     "exact_version_basis": "Arena model_name %s mapped by hand" % row["model_name"]}
            en = ("LMArena %s leaderboard (category overall), published %s; model %s; %s votes; 95%% interval %s–%s. CC BY 4.0, lmarena-ai/leaderboard-dataset @%s." %
                  (subset, row["leaderboard_publish_date"], row["model_name"], row.get("vote_count"), fmt(dec(row["rating_lower"]), 1), fmt(dec(row["rating_upper"]), 1), ARENA_REV[:12]))
            ru = ("Лидерборд LMArena %s (категория overall) от %s; модель %s; голосов: %s; 95%% интервал %s–%s. CC BY 4.0, lmarena-ai/leaderboard-dataset @%s." %
                  (subset, row["leaderboard_publish_date"], row["model_name"], row.get("vote_count"), fmt(dec(row["rating_lower"]), 1), fmt(dec(row["rating_upper"]), 1), ARENA_REV[:12]))
            col.add(rid, **{"Benchmark": bench, "Protocol": "%s; lmarena-ai/leaderboard-dataset %s; overall; Bradley–Terry" % (bench, subset),
                            "Benchmark Category": category, "Unit": "Arena score", "Higher Is Better": "YES", "Score": fmt(rating, 2),
                            "Evaluator": "LMArena", "Result Kind": "independent", "Independent": "YES", "Public": "YES",
                            "Measured": row["leaderboard_publish_date"], "Configuration": config,
                            "Confidence Low": fmt(dec(row["rating_lower"]), 2), "Confidence High": fmt(dec(row["rating_upper"]), 2),
                            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra, "Source URL": ARENA_URL,
                            "Source Model": row["model_name"], "Source Record ID": "lmarena:%s:%s:%s:%s" % (ARENA_REV[:12], subset, row["model_name"], row["leaderboard_publish_date"]),
                            "Snapshot": "lmarena-ai/leaderboard-dataset@%s latest" % ARENA_REV[:12], "Source SHA256": payload["sha256"]})


AIDER_BENCH = {"polyglot_leaderboard.yml": ("Aider Polyglot", "pass_rate_2"), "edit_leaderboard.yml": ("Aider Code Editing", "pass_rate_2"),
               "refactor_leaderboard.yml": ("Aider Refactoring", "pass_rate_1")}
ALIAS_WINDOWS = {"gpt-4o": ("2024-05-13", "2024-10-01"), "o1": ("2024-12-17", None), "o1-mini": ("2024-09-12", None)}


def collect_aider(col, report):
    names = {}
    for rid, spec in MAP.items():
        for name in spec.get("aider", []):
            names[name] = rid
    commit = (AUDIT / "aider/COMMIT").read_text().strip()
    for filename, (bench, field) in AIDER_BENCH.items():
        path = AUDIT / "aider" / filename
        file_hash = sha(path)
        for block in path.read_text(encoding="utf-8").split("\n- dirname:")[0:]:
            fields = dict(re.findall(r"\n  (\w+): (.*)", "\n" + block))
            model = (fields.get("model") or "").strip()
            rid = names.get(model)
            if not rid:
                continue
            date = (fields.get("date") or "").strip()
            if model in ALIAS_WINDOWS:
                start, end = ALIAS_WINDOWS[model]
                if date < start or (end and date > end):
                    col.skipped["aider alias outside snapshot window"] += 1
                    continue
            value = dec(fields.get(field) or fields.get("pass_rate_2") or fields.get("pass_rate_1"))
            if value is None:
                continue
            dirname = block.split("\n", 1)[0].replace("- dirname:", "").strip()
            command = (fields.get("command") or "").strip().strip('"')
            fmt_edit = (fields.get("edit_format") or "").strip()
            extra = {"source_score": str(value), "source_unit": "percent of test cases passed", "bounded_range": [0, 100], "normalized_percent": fmt(value),
                     "normalization_method": "none (source is a percentage)", "rating_eligible": True, "rating_exclusion_reason": None,
                     "evaluator_type": "independent open-source benchmark maintainer", "evaluator_family": "Aider",
                     "licence": "Apache-2.0 (Aider-AI/aider repository data)", "command": command, "edit_format": fmt_edit,
                     "aider_version": fields.get("versions"), "test_cases": fields.get("test_cases"), "cost_usd": fields.get("total_cost"),
                     "exact_version_basis": "Aider model label %s (run %s) mapped by hand" % (model, date)}
            en = "Aider %s leaderboard; model label %s; %s = %s%%; edit format %s; command `%s`; run %s. Apache-2.0, Aider-AI/aider @%s." % (
                bench, model, field, value, fmt_edit, command, date, commit[:12])
            ru = "Лидерборд Aider %s; метка модели %s; %s = %s%%; формат правок %s; команда `%s`; прогон %s. Apache-2.0, Aider-AI/aider @%s." % (
                bench, model, field, value, fmt_edit, command, date, commit[:12])
            col.add(rid, **{"Benchmark": bench, "Protocol": "%s; Aider leaderboard; %s" % (bench, field), "Benchmark Category": "text", "Unit": "%",
                            "Higher Is Better": "YES", "Score": fmt(value), "Evaluator": "Aider", "Result Kind": "independent", "Independent": "YES",
                            "Public": "YES", "Measured": date, "Configuration": ("edit format %s" % fmt_edit) + (" ; " + model.split("(", 1)[1].rstrip(")") if "(" in model else ""),
                            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra,
                            "Source URL": "https://github.com/Aider-AI/aider/blob/%s/aider/website/_data/%s" % (commit, filename),
                            "Source Model": model, "Source Record ID": "aider:%s:%s" % (filename, dirname or model + ":" + date),
                            "Snapshot": "Aider-AI/aider@%s" % commit[:12], "Source SHA256": file_hash})


ASR_FILES = {"english_short_latest.csv": ("Open ASR Leaderboard (English short-form, mean WER)", "avg"),
             "multilingual_latest.csv": (None, None), "longform_latest.csv": ("Open ASR Leaderboard (long-form, mean WER)", "Average")}


def collect_asr(col, report):
    names = {}
    for rid, spec in MAP.items():
        for name in spec.get("open_asr", []):
            names[name] = rid
    for filename, (bench, field) in ASR_FILES.items():
        if not bench:
            report["skipped_files"]["open_asr:" + filename] = "per-language WER only; no published aggregate"
            continue
        path = AUDIT / "open_asr" / filename
        file_hash = sha(path)
        for row in csv.DictReader(open(path, encoding="utf-8")):
            model = (row.get("model") or row.get("model_id") or "").strip()
            rid = names.get(model)
            if not rid:
                continue
            value = dec(row.get(field))
            if value is None:
                continue
            config = "decoding fast-gpu-asr" if "fast-gpu-asr" in model else ("Transformers-format checkpoint (-hf)" if model.endswith("-hf") else "default")
            extra = {"source_score": str(row.get(field)), "source_unit": "WER % (lower is better, unbounded above)", "bounded_range": None, "normalized_percent": None,
                     "normalization_method": "not converted (error rate)", "rating_eligible": False, "rating_exclusion_reason": "not republishable (no licence on result datasets)",
                     "evaluator_type": "independent leaderboard (Hugging Face audio team; NVIDIA co-authors the methodology paper)", "evaluator_family": "Hugging Face Open ASR Leaderboard",
                     "licence": "hf-audio result datasets carry no licence", "rtfx": row.get("RTFx"),
                     "exact_version_basis": "Hugging Face model id %s" % model}
            en = "Hugging Face Open ASR Leaderboard; %s; model %s; mean WER %s%% (RTFx %s). Result dataset hf-audio (pinned revision), no licence stated." % (filename, model, fmt(value, 2), row.get("RTFx"))
            ru = "Hugging Face Open ASR Leaderboard; %s; модель %s; средний WER %s%% (RTFx %s). Датасет результатов hf-audio (зафиксированная ревизия), лицензия не указана." % (filename, model, fmt(value, 2), row.get("RTFx"))
            col.add(rid, **{"Benchmark": bench, "Protocol": "%s; column %s" % (bench, field), "Benchmark Category": "audio", "Unit": "WER %",
                            "Higher Is Better": "NO", "Score": fmt(value, 3), "Evaluator": "Hugging Face Open ASR Leaderboard", "Result Kind": "independent",
                            "Independent": "YES", "Public": "NO", "Measured": "", "Configuration": config,
                            "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra, "Source URL": ASR_URL,
                            "Source Model": model, "Source Record ID": "open_asr:%s:%s" % (filename, model), "Snapshot": "hf-audio result datasets pinned 2026-09-25",
                            "Source SHA256": file_hash})


TTS_URL = "https://huggingface.co/spaces/TTS-AGI/TTS-Arena-V2"


def collect_tts_arena(col, report):
    names = {n: rid for rid, spec in MAP.items() for n in spec.get("tts_arena", [])}
    path = AUDIT / "tts_arena/leaderboard.json"
    file_hash = sha(path)
    for row in json.loads(path.read_text(encoding="utf-8"))["rows"]:
        rid = names.get(row["id"])
        if not rid:
            continue
        elo, unc = dec(row["elo"]), dec(row["uncertainty"])
        extra = {"source_score": str(row["elo"]), "source_unit": "Elo (unbounded)", "bounded_range": None, "normalized_percent": None,
                 "normalization_method": "not normalizable (relative preference scale)", "rating_eligible": False,
                 "rating_exclusion_reason": "not republishable (leaderboard data carry no licence; Space code Apache-2.0 only)",
                 "evaluator_type": "independent leaderboard (human pairwise preference)", "evaluator_family": "TTS Arena (TTS-AGI)",
                 "licence": "no licence for leaderboard data", "win_rate": row.get("winRate"), "votes": row.get("totalVotes"),
                 "rank": row.get("rank"), "tier": row.get("tier"), "preliminary": row.get("preliminary"),
                 "exact_version_basis": "TTS Arena model id %s mapped by hand" % row["id"]}
        en = "TTS Arena V2 leaderboard (api/leaderboard, fetched 2026-09-27); model %s (%s); Elo %s ± %s; %s votes. Leaderboard data carry no licence." % (row["name"], row["id"], row["elo"], row["uncertainty"], row.get("totalVotes"))
        ru = "Лидерборд TTS Arena V2 (api/leaderboard, получено 2026-09-27); модель %s (%s); Elo %s ± %s; голосов: %s. Лицензии на данные лидерборда нет." % (row["name"], row["id"], row["elo"], row["uncertainty"], row.get("totalVotes"))
        col.add(rid, **{"Benchmark": "TTS Arena V2", "Protocol": "TTS Arena V2; blind pairwise human preference; Elo", "Benchmark Category": "audio",
                        "Unit": "Elo", "Higher Is Better": "YES", "Score": fmt(elo, 0), "Evaluator": "TTS Arena (TTS-AGI)", "Result Kind": "independent",
                        "Independent": "YES", "Public": "NO", "Measured": CHECKED, "Configuration": "default",
                        "Confidence Low": fmt(elo - unc, 0), "Confidence High": fmt(elo + unc, 0),
                        "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra, "Source URL": TTS_URL,
                        "Source Model": row["id"], "Source Record ID": "tts_arena:%s:%s" % (CHECKED, row["id"]),
                        "Snapshot": "TTS Arena V2 api/leaderboard fetched 2026-09-27", "Source SHA256": file_hash})


MTEB_MODELS = {"Qwen__Qwen3-Embedding-0.6B": "qwen3-embedding-06b-77ca7a9a", "Qwen__Qwen3-Embedding-4B": "qwen3-embedding-4b-25996213",
               "Qwen__Qwen3-Embedding-8B": "qwen3-embedding-8b-03fb42a9"}
MTEB_DEVELOPER_COMMITS = {"eca561f4"}  # "Add results for Qwen3-Embedding series models" (#214), release-day submission
MTEB_PERCENT_TYPES = ("Classification", "Retrieval", "Clustering", "PairClassification", "Reranking", "BitextMining", "InstructionRetrieval")


def collect_mteb(col, report):
    import subprocess
    repo = AUDIT / "mteb-results"
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    prov, current = {}, None
    for line in open(AUDIT / "mteb_provenance.txt", encoding="utf-8"):
        line = line.strip()
        if line.startswith("@@"):
            current = line[2:]
        elif line:
            prov[line] = current
    for path, commit in sorted(prov.items()):
        folder = path.split("/")[1]
        rid = MTEB_MODELS.get(folder)
        if not rid or path.endswith("model_meta.json") or not (repo / path).exists():
            continue
        sha_c, author, subject = commit.split("|", 2)
        if sha_c in MTEB_DEVELOPER_COMMITS:
            col.skipped["mteb: developer release submission (not imported)"] += 1
            continue
        try:
            data = json.loads((repo / path).read_text(encoding="utf-8"))
        except ValueError:
            col.skipped["mteb: unreadable file"] += 1
            continue
        scores = data.get("scores") or {}
        if len(scores) != 1 or len(next(iter(scores.values()))) != 1:
            col.skipped["mteb: multi split/subset (no single published main score)"] += 1
            continue
        split, entries = next(iter(scores.items()))
        entry = entries[0]
        main = dec(entry.get("main_score"))
        if main is None:
            continue
        task = data.get("task_name") or Path(path).stem
        percent_ok = task.endswith(MTEB_PERCENT_TYPES) and Decimal(0) <= main <= Decimal(1)
        extra = {"source_score": str(entry.get("main_score")), "source_unit": "MTEB main_score (task-type metric)",
                 "bounded_range": [0, 1] if percent_ok else None, "normalized_percent": fmt(main * 100) if percent_ok else None,
                 "normalization_method": "score × 100 (exact)" if percent_ok else "not converted (correlation-type or unbounded metric)",
                 "rating_eligible": bool(percent_ok), "rating_exclusion_reason": None if percent_ok else "metric type not a bounded 0–1 score",
                 "evaluator_type": "independent contributor to MTEB results (not the developer submission)", "evaluator_family": "MTEB community contributors",
                 "licence": "CC0-1.0 (embeddings-benchmark/results)", "contribution": subject, "commit": sha_c, "split": split,
                 "hf_subset": entry.get("hf_subset"), "languages": entry.get("languages"), "mteb_version": data.get("mteb_version"),
                 "dataset_revision": data.get("dataset_revision"), "model_revision": path.split("/")[2],
                 "exact_version_basis": "MTEB results folder %s (model revision %s)" % (folder, path.split("/")[2])}
        en = "MTEB task %s (%s, subset %s); main score %s; community run from '%s' (commit %s), not the developer's release submission; CC0." % (task, split, entry.get("hf_subset"), entry.get("main_score"), subject, sha_c)
        ru = "Задача MTEB %s (%s, subset %s); main score %s; прогон сообщества из «%s» (commit %s), не сабмит разработчика; CC0." % (task, split, entry.get("hf_subset"), entry.get("main_score"), subject, sha_c)
        col.add(rid, **{"Benchmark": "MTEB: %s" % task, "Protocol": "MTEB task %s; main_score; split %s; subset %s" % (task, split, entry.get("hf_subset")),
                        "Benchmark Category": "text", "Unit": "main score", "Higher Is Better": "YES", "Score": fmt(main, 6),
                        "Evaluator": "MTEB community contributors", "Result Kind": "independent", "Independent": "YES", "Public": "YES",
                        "Measured": "", "Configuration": "default", "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": extra,
                        "Source URL": "https://github.com/embeddings-benchmark/results/blob/%s/%s" % (head, path),
                        "Source Model": folder.replace("__", "/"), "Source Record ID": "mteb:%s:%s" % (head[:12], path),
                        "Snapshot": "embeddings-benchmark/results@%s" % head[:12], "Source SHA256": sha(repo / path)})


# --------------------------------------------------------------------- status facts

SOURCES_CHECKED = [
    "Epoch AI benchmarking hub snapshot 2026-09-27 (own runs + 70 external leaderboards)",
    "lmarena-ai/leaderboard-dataset @%s (text, vision, webdev, document, text-to-image, image-edit, text/image-to-video, video-edit)" % ARENA_REV[:12],
    "Aider leaderboards (polyglot, code editing, refactoring)",
    "Hugging Face Open ASR Leaderboard result datasets (English short-form, multilingual, long-form)",
    "MTEB results repository (embeddings)",
    "TTS Arena V2 public leaderboard (text-to-speech)",
]
NEXT_STEP = {
    "text": "Re-check new Epoch AI hub and LMArena snapshots; for open weights look for independent academic evaluations (HELM, OpenCompass) with a stated results licence.",
    "image": "Re-check lmarena-ai/leaderboard-dataset text_to_image/image_edit/vision subsets; academic benchmarks (GenEval, HEIM) only if the exact checkpoint was evaluated.",
    "video": "Re-check lmarena-ai/leaderboard-dataset text_to_video/image_to_video subsets and VBench leaderboard (results licence to verify).",
    "audio": "STT: Open ASR Leaderboard (licence missing) / TTS: TTS Arena V2 (licence to verify); music/SFX: no mature independent benchmark with open results.",
    "other": "No mature independent benchmark ecosystem with open results for this task type (robotics, 3D, motion, safety classifiers, protein structure); monitor peer-reviewed comparisons.",
}


def build_status(rows, models, candidates):
    evals = collections.defaultdict(list)
    for row in rows["Evaluations"]:
        evals[row["Record ID"]].append(row)
    out = {}
    for rid, model in models.items():
        mine = evals.get(rid, [])
        pub_ind = [e for e in mine if e.get("Independent") == "YES" and e.get("Public") == "YES" and e.get("Result Kind") == "independent"]
        ind = [e for e in mine if e.get("Independent") == "YES" and e.get("Result Kind") == "independent"]
        dev = [e for e in mine if e.get("Result Kind") == "developer" or (e.get("Independent") == "NO" and e.get("Result Kind") != "composite")]
        category = model.get("Category") or "text"
        names = [model.get("Name")] + [a.strip() for a in (model.get("Aliases") or "").split("|") if a.strip()]
        evidence = {"searched_names": names, "record_id": rid, "checked": CHECKED, "checked_sources": SOURCES_CHECKED,
                    "independent_rows": len(ind), "public_independent_rows": len(pub_ind),
                    "public_independent_evaluators": sorted({e["Evaluator"] for e in pub_ind}),
                    "independent_not_public_evaluators": sorted({e["Evaluator"] for e in ind if e.get("Public") != "YES"}),
                    "developer_reported_rows": len(dev)}
        rejected = candidates.get(rid) or []
        if rejected:
            evidence["rejected_source_names"] = rejected[:20]
        if rid in CONFIGURATION_OF:
            parent, config = CONFIGURATION_OF[rid]
            status, en, ru = "not_applicable", ("Configuration card of %s (reasoning effort %s); independent results are recorded on %s with Configuration=%s to avoid duplicate observations." % (parent, config, parent, config)), \
                ("Карточка конфигурации %s (reasoning effort %s); независимые результаты записаны на %s с Configuration=%s, без дублирования наблюдений." % (parent, config, parent, config))
        elif pub_ind:
            status, en, ru = "available", "Publishable independent evaluations of the exact version: %s." % ", ".join(evidence["public_independent_evaluators"]), \
                "Публикуемые независимые оценки точной версии: %s." % ", ".join(evidence["public_independent_evaluators"])
        elif ind:
            status = "found_but_not_republishable"
            en = "Independent evaluations of the exact version exist (%s) but their licences do not allow republication; kept as internal evidence (Public=NO)." % ", ".join(evidence["independent_not_public_evaluators"])
            ru = "Независимые оценки точной версии есть (%s), но лицензии не разрешают републикацию; сохранены как внутреннее evidence (Public=NO)." % ", ".join(evidence["independent_not_public_evaluators"])
        elif rid in NOT_EXACT:
            status, en = "exact_version_not_found", NOT_EXACT[rid]
            ru = "Найдены только результаты другой версии/варианта: " + NOT_EXACT[rid]
        elif model.get("Decision Code") == "IDENTITY" or model.get("Publication Decision") == "ARCHIVE":
            status = "identity_ambiguous" if model.get("Decision Code") == "IDENTITY" else "not_applicable"
            if status == "identity_ambiguous":
                en = "Master identity is not settled (Decision Code IDENTITY); results are not attached to an unconfirmed version."
                ru = "Идентичность записи в master не закрыта (Decision Code IDENTITY); результаты к неподтверждённой версии не прикрепляются."
            else:
                en = "ARCHIVE record (%s); evaluations belong to the canonical card %s." % (model.get("Decision Code"), model.get("Canonical / Parent Record ID") or "")
                ru = "Архивная запись (%s); оценки относятся к канонической карточке %s." % (model.get("Decision Code"), model.get("Canonical / Parent Record ID") or "")
        elif dev:
            status = "only_developer_reported"
            en, ru = "Only developer-reported results were found for the exact version.", "Для точной версии найдены только результаты разработчика."
        else:
            status = "gap"
            en = "No independent evaluation of the exact version in the checked sources (%s)." % category
            ru = "В проверенных источниках нет независимой оценки точной версии (%s)." % category
        evidence.update(status=status, reason_en=en, reason_ru=ru, next_step=None if status == "available" else NEXT_STEP.get(category, NEXT_STEP["other"]))
        out[rid] = evidence
    return out


# --------------------------------------------------------------------- main


def rejected_candidates(models):
    """Source names that share the card's name tokens but were not mapped (for evidence only)."""
    path = ROOT / "artifacts/eval-audit-2026-09-27/source_names.json"
    if not path.exists():
        return {}
    names = json.loads(path.read_text(encoding="utf-8"))
    mapped = {n for spec in MAP.values() for key in ("epoch", "arena", "aider", "open_asr", "tts_arena") for n in spec.get(key, [])}
    out = {}
    for rid, model in models.items():
        stem = re.sub(r"[^a-z0-9]", "", (model.get("Name") or "").lower())
        if len(stem) < 4:
            continue
        hits = []
        for source, values in names.items():
            for value in values:
                if stem in re.sub(r"[^a-z0-9]", "", value.lower()) and value not in mapped:
                    hits.append("%s:%s" % (source, value))
        if hits:
            out[rid] = sorted(hits)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", default=str(AUDIT / "audit_data.json"))
    args = parser.parse_args()
    book = Path(args.book)
    before_sha = sha(book)
    rows, meta, extra = cm.read_workbook(book)
    stamp = cm.now_utc()
    log = rows["Changelog"]
    models = {r["Record ID"]: r for r in rows["Models"]}
    for rid in MAP:
        assert rid in models, rid
    report = {"skipped_files": {}, "before_sha256": before_sha}
    col = Collector(rows, models)
    collect_epoch(col, report)
    collect_arena(col, report)
    collect_aider(col, report)
    collect_asr(col, report)
    collect_mteb(col, report)
    collect_tts_arena(col, report)
    columns = list(rows["Evaluations"][0].keys())
    secondary = collections.defaultdict(list)
    for dup_id, kept_id in col.duplicates:
        secondary[kept_id].append(dup_id)
    for new in col.out + col.updates:
        if isinstance(new["Conditions Extra (JSON)"], dict) and secondary.get(new["Source Record ID"]):
            new["Conditions Extra (JSON)"]["secondary_source_rows"] = sorted(secondary[new["Source Record ID"]])
    # corrections of rows written by an earlier pass of this run (classification fixes), logged field by field
    corrected = removed = 0
    for new in col.updates:
        new["Conditions Extra (JSON)"] = json.dumps(new["Conditions Extra (JSON)"], ensure_ascii=False, sort_keys=True)
        existing = col.run_rows[new["Source Record ID"]]
        for field, value in new.items():
            value = "" if value is None else str(value)
            if field in columns and existing.get(field, "") != value:
                log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": existing["Record ID"], "Field": "%s (%s)" % (field, existing["Key"]),
                            "Before": str(existing.get(field, ""))[:1500], "After": value[:1500], "Reason": "%s: correction of this run's row (developer/independence classification, evidence)" % RUN})
                existing[field] = value
                corrected += 1
    # rows of this run that turned out to repeat an observation already kept are removed (never rows of earlier runs)
    drop = {dup_id for dup_id, _ in col.duplicates if dup_id in col.run_rows}
    if drop:
        kept = []
        for row in rows["Evaluations"]:
            if RUN in (row.get("Key") or "") and row.get("Source Record ID") in drop:
                log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "row removed (%s)" % row["Key"],
                            "Before": ("%s | %s | %s | %s" % (row["Benchmark"], row["Score"], row["Evaluator"], row["Source Record ID"]))[:500], "After": "",
                            "Reason": "%s: duplicate of an observation kept under another source row of the same aggregator (added earlier in this run)" % RUN})
                removed += 1
                continue
            kept.append(row)
        rows["Evaluations"][:] = kept
    # rating-readiness fields for rows of earlier runs that carry none; Score, Unit and every other field stay as they are
    backfilled = 0
    for row in rows["Evaluations"]:
        if RUN in (row.get("Key") or "") or (row.get("Conditions Extra (JSON)") or "").strip() not in ("", "{}", '{"additional_checks": ""}'):
            continue
        evaluator, kind = row.get("Evaluator") or "", row.get("Result Kind") or ""
        if evaluator == "Epoch AI" and kind == "independent" and row.get("Unit") == "%":
            extra_row = {"source_score": row["Score"], "source_unit": "percent (stored at import as Epoch fraction × 100)", "bounded_range": [0, 100],
                         "normalized_percent": row["Score"], "normalization_method": "score × 100 at import (exact up to 0.001 rounding)",
                         "rating_eligible": row.get("Public") == "YES", "rating_exclusion_reason": None if row.get("Public") == "YES" else "not republishable",
                         "evaluator_type": "independent benchmark organization", "evaluator_family": "Epoch AI", "licence": "CC BY 4.0 (Epoch AI own evaluation)"}
        elif kind == "composite":
            extra_row = {"source_score": row["Score"], "source_unit": row.get("Unit") or "index", "normalized_percent": None,
                         "normalization_method": "not normalizable (composite index)", "rating_eligible": False,
                         "rating_exclusion_reason": "composite index mixing own, third-party and developer-reported results",
                         "evaluator_type": "composite index", "evaluator_family": evaluator}
        elif evaluator == "Artificial Analysis":
            extra_row = {"source_score": row["Score"], "source_unit": row.get("Unit") or "points", "normalized_percent": None,
                         "normalization_method": "not normalizable (proprietary index / unbounded)", "rating_eligible": False,
                         "rating_exclusion_reason": "not republishable (Artificial Analysis terms block republication)",
                         "evaluator_type": "independent benchmark organization", "evaluator_family": "Artificial Analysis",
                         "licence": "Artificial Analysis terms block republication"}
        else:
            continue
        previous = row.get("Conditions Extra (JSON)") or ""
        if previous.strip() and previous.strip() != "{}":
            extra_row.update(json.loads(previous))
        value = json.dumps(extra_row, ensure_ascii=False, sort_keys=True)
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "Conditions Extra (JSON) (%s)" % row["Key"],
                    "Before": previous, "After": value[:1500], "Reason": "%s: rating-readiness fields added; score and other fields unchanged" % RUN})
        row["Conditions Extra (JSON)"] = value
        backfilled += 1
    report.update({"corrected_fields": corrected, "removed_duplicates_of_this_run": removed, "backfilled_rating_fields": backfilled})
    for new in col.out:
        new["Conditions Extra (JSON)"] = json.dumps(new["Conditions Extra (JSON)"], ensure_ascii=False, sort_keys=True)
        row = {c: "" for c in columns}
        row.update({k: ("" if v is None else str(v)) for k, v in new.items()})
        rows["Evaluations"].append(row)
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": row["Record ID"], "Field": "row added (%s)" % row["Key"],
                    "Before": "", "After": "%s | %s %s | %s | Independent=%s Public=%s | %s" % (row["Benchmark"], row["Score"], row["Unit"], row["Evaluator"],
                                                                                           row["Independent"], row["Public"], row["Source Record ID"])[:500],
                    "Reason": "%s: independent-evaluation audit, exact version mapped by hand" % RUN})
    status = build_status(rows, models, rejected_candidates(models))
    facts_by_key = {(f["Record Type"], f["Record ID"], f["Fact"]): f for f in rows["Facts"] if f.get("Fact") == "independent_evaluation_status"}
    fact_columns = list(rows["Facts"][0].keys())
    changed_facts = added_facts = 0
    for rid, evidence in status.items():
        value = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
        existing = facts_by_key.get(("model", rid, "independent_evaluation_status"))
        if existing is not None:
            if existing["Value (JSON)"] != value:
                log.append({"Timestamp (UTC)": stamp, "Sheet": "Facts", "Record ID": rid, "Field": "Value (JSON) (%s)" % existing["Key"],
                            "Before": existing["Value (JSON)"][:1500], "After": value[:1500], "Reason": "%s: status re-derived from the audited evaluation layer" % RUN})
                existing.update({"Value (JSON)": value, "Checked": CHECKED, "Source URL": existing.get("Source URL") or "https://epoch.ai/benchmarks"})
                changed_facts += 1
            continue
        key = "fact-%s-independent_evaluation_status-%s" % (RUN, rid)
        row = {c: "" for c in fact_columns}
        row.update({"Key": key[:120], "Record Type": "model", "Record ID": rid, "Fact": "independent_evaluation_status", "Value (JSON)": value,
                    "Source URL": "https://epoch.ai/benchmarks/use-this-data" if evidence["status"] != "available" else "https://epoch.ai/benchmarks",
                    "Checked": CHECKED})
        rows["Facts"].append(row)
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Facts", "Record ID": rid, "Field": "row added (%s)" % row["Key"], "Before": "",
                    "After": value[:1500], "Reason": "%s: evidenced independent_evaluation_status" % RUN})
        added_facts += 1
    report.update({"added_evaluations": len(col.out), "skipped": dict(col.skipped), "facts_added": added_facts, "facts_changed": changed_facts,
                   "status_counts": dict(collections.Counter(v["status"] for v in status.values())),
                   "status": status, "rows": col.out})
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("status", "rows")}, ensure_ascii=False, indent=1, default=str))
    if args.dry_run:
        print("dry run: workbook not written")
        return
    meta = dict(meta)
    meta.update({"Verification run": "%s — independent evaluations audit (Evaluations, Facts)" % RUN})
    meta = cm.refresh_meta(meta, rows, stamp)
    cm.write_workbook(rows, meta, book, extra)
    print(json.dumps({"after_sha256": sha(book)}, indent=1))


if __name__ == "__main__":
    main()
