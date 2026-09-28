"""Stage 2 of the 2026-09-27 evaluation audit: hand-transcribed evidence for the PUBLISHED
models that had no public independent evaluation after stage 1.

Every value below was copied from the named primary source (saved with SHA-256 under
artifacts/eval-audit-2026-09-27/stage2/pages/<page>.raw) for the exact model version.
``kind``: "developer" (the model's own developer published it; Independent=NO) or
"independent" (a third party ran it). Developer results are never rating inputs of the
Independent Rating. Nothing here is estimated or derived except where ``note`` says so.

OBS rows: (record_id, source_key, benchmark, score, unit, higher_is_better, configuration, category, note)
STATUS: record_id -> {"status": ..., "found_en": ..., "found_ru": ..., "checked": [urls]} for models
without any numeric row (or to explain a decision).
"""

import json
import os

# key -> (url, saved page, evaluator, kind, public, title)
SOURCES = {
    "qwen3-asr-card": ("https://huggingface.co/Qwen/Qwen3-ASR-1.7B", "qwen3-asr-17b", "Alibaba Qwen", "developer", True,
                       "Qwen3-ASR model card (benchmark tables)"),
    "qwen3-reranker-card": ("https://huggingface.co/Qwen/Qwen3-Reranker-8B", "qwen3-reranker-8b", "Alibaba Qwen", "developer", True,
                            "Qwen3-Reranker model card, Evaluation (our runs on top-100 candidates of Qwen3-Embedding-0.6B)"),
}

WER = "WER %"
NDCG = "points (nDCG@10 ×100)"

OBS = [
    # Qwen3-ASR (developer): public datasets, WER ↓
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "LibriSpeech test-clean", "1.63", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "LibriSpeech test-other", "3.38", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "GigaSpeech", "8.45", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "FLEURS (en)", "3.35", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "FLEURS (zh)", "2.41", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "MLS (multilingual)", "8.55", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-17b-d158d43f", "qwen3-asr-card", "Common Voice (multilingual)", "9.18", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "LibriSpeech test-clean", "2.11", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "LibriSpeech test-other", "4.55", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "GigaSpeech", "8.88", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "FLEURS (en)", "4.39", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "FLEURS (zh)", "2.88", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "MLS (multilingual)", "13.19", WER, "NO", "offline", "audio", ""),
    ("qwen3-asr-06b-504c078f", "qwen3-asr-card", "Common Voice (multilingual)", "12.75", WER, "NO", "offline", "audio", ""),
    # Qwen3-Reranker (developer)
    ("qwen3-reranker-06b-93dd8291", "qwen3-reranker-card", "MTEB-R (retrieval subsets of MTEB eng v2)", "65.80", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-06b-93dd8291", "qwen3-reranker-card", "CMTEB-R", "71.31", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-06b-93dd8291", "qwen3-reranker-card", "MMTEB-R", "66.36", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-06b-93dd8291", "qwen3-reranker-card", "MLDR", "67.28", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-06b-93dd8291", "qwen3-reranker-card", "MTEB-Code", "73.42", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-4b-b9e9a594", "qwen3-reranker-card", "MTEB-R (retrieval subsets of MTEB eng v2)", "69.76", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-4b-b9e9a594", "qwen3-reranker-card", "CMTEB-R", "75.94", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-4b-b9e9a594", "qwen3-reranker-card", "MMTEB-R", "72.74", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-4b-b9e9a594", "qwen3-reranker-card", "MLDR", "69.97", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-4b-b9e9a594", "qwen3-reranker-card", "MTEB-Code", "81.20", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-8b-2233bb1b", "qwen3-reranker-card", "MTEB-R (retrieval subsets of MTEB eng v2)", "69.02", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-8b-2233bb1b", "qwen3-reranker-card", "CMTEB-R", "77.45", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-8b-2233bb1b", "qwen3-reranker-card", "MMTEB-R", "72.94", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-8b-2233bb1b", "qwen3-reranker-card", "MLDR", "70.19", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
    ("qwen3-reranker-8b-2233bb1b", "qwen3-reranker-card", "MTEB-Code", "81.22", NDCG, "YES", "rerank top-100 of Qwen3-Embedding-0.6B", "text", ""),
]

STATUS = {}


def src(key, url, page, evaluator, title, kind="developer", public=True):
    SOURCES[key] = (url, page, evaluator, kind, public, title)


def add(rid, source_key, category, configuration, unit, higher, pairs, note=""):
    """pairs: [(benchmark, score_as_published)]; unit "%frac" = published as 0–1 fraction (stored ×100)."""
    for bench, score in pairs:
        OBS.append((rid, source_key, bench, score, unit, higher, configuration, category, note))


PCT, FRAC, PTS = "%", "%frac", "points"

# ---- Aleph Alpha Pharia-1 (one card documents both versions)
src("pharia-card", "https://huggingface.co/Aleph-Alpha/Pharia-1-LLM-7B-control", "hf_Aleph-Alpha_Pharia-1-LLM-7B-control", "Aleph Alpha",
    "Pharia-1-LLM-7B-control model card, benchmark table (lm-eval few-shot)")
add("pharia-1-llm-7b-control-ea3eb74f", "pharia-card", "text", "few-shot per table", FRAC, "YES",
    [("ARC-Challenge (25-shot, acc_norm)", "0.546"), ("MMLU (5-shot)", "0.484"), ("GSM8K (5-shot)", "0.014"), ("HellaSwag (10-shot, acc_norm)", "0.646"),
     ("WinoGrande (5-shot)", "0.651"), ("MMLU-DE (5-shot)", "0.428"), ("HellaSwag-DE (10-shot, acc_norm)", "0.487")])
add("pharia-1-llm-7b-control-aligned-34e1d5a0", "pharia-card", "text", "few-shot per table", FRAC, "YES",
    [("ARC-Challenge (25-shot, acc_norm)", "0.528"), ("MMLU (5-shot)", "0.525"), ("GSM8K (5-shot)", "0.163"), ("HellaSwag (10-shot, acc_norm)", "0.761"),
     ("WinoGrande (5-shot)", "0.643"), ("MMLU-DE (5-shot)", "0.488"), ("HellaSwag-DE (10-shot, acc_norm)", "0.633")])

# ---- LG AI Research
src("exaone45-card", "https://huggingface.co/LGAI-EXAONE/EXAONE-4.5-33B", "hf_LGAI-EXAONE_EXAONE-4.5-33B", "LG AI Research",
    "EXAONE 4.5 33B model card, evaluation tables (reasoning mode)")
add("exaone-45-33b-497b830b", "exaone45-card", "image", "reasoning", PCT, "YES",
    [("MMMU", "78.7"), ("MMMU-Pro", "68.6"), ("MathVista (mini)", "85.0"), ("AI2D", "89.0"), ("OCRBench v2", "63.2"), ("MMStar", "74.9")])
add("exaone-45-33b-497b830b", "exaone45-card", "text", "reasoning", PCT, "YES",
    [("AIME 2025", "92.9"), ("GPQA Diamond", "80.5"), ("LiveCodeBench v6", "81.4"), ("MMLU-Pro", "83.3"), ("IFEval", "89.6"), ("KMMLU-Pro", "67.6")])
src("kexaone2-card", "https://huggingface.co/LGAI-EXAONE/K-EXAONE-2.0-750B-A37B", "hf_LGAI-EXAONE_K-EXAONE-2.0-750B-A37B", "LG AI Research",
    "K-EXAONE 2.0 model card, evaluation table")
add("k-exaone-20-750b-a37b-da64adc6", "kexaone2-card", "text", "default (as reported)", PCT, "YES",
    [("MMLU-Pro", "83.5"), ("GPQA Diamond", "82.2"), ("Humanity's Last Exam", "18.3"), ("AIME 2026", "92.3"), ("SWE-bench Verified", "68.2"),
     ("Terminal-Bench 2.1", "43.8"), ("IFEval", "92.4"), ("KMMLU-Pro", "69.1"), ("MMMLU", "86.6")])

# ---- ai-sage GigaChat 3.5 Reasoning (card table column "GigaChat 3.5 Ultra Reasoning" = this 432B model)
src("gigachat35-card", "https://huggingface.co/ai-sage/GigaChat3.5-432B-A28B-reasoning", "hf_ai-sage_GigaChat3.5-432B-A28B-reasoning", "SberDevices (ai-sage)",
    "GigaChat 3.5 Reasoning model card, evaluation table")
add("gigachat-35-432b-a28b-reasoning-02085d96", "gigachat35-card", "text", "reasoning", PCT, "YES",
    [("AIME 2025 (mean@32)", "89"), ("AIME 2026 (mean@32)", "92"), ("HMMT 2025 (mean@8)", "83.13"), ("GPQA Diamond", "82.32"), ("IFBench", "77"),
     ("LiveCodeBench v6", "85.4"), ("SWE-bench Verified (mini-swe-agent)", "64.7"), ("Terminal-Bench 2 (mini-swe-agent)", "30.3"), ("MERA-2.0", "42.3")])

# ---- AI21 Jamba (base model, v0.1)
src("jamba-card", "https://huggingface.co/ai21labs/Jamba-v0.1", "hf_ai21labs_Jamba-v0.1", "AI21 Labs", "Jamba-v0.1 model card, results on common benchmarks")
add("jamba-29e33df6", "jamba-card", "text", "base model", PCT, "YES",
    [("HellaSwag", "87.1"), ("ARC-Challenge", "64.4"), ("WinoGrande", "82.5"), ("PIQA", "83.2"), ("MMLU", "67.4"), ("BBH", "45.4"),
     ("TruthfulQA", "46.4"), ("GSM8K (CoT)", "59.9")])

# ---- Black Forest Labs FLUX 3 Action (DROID card)
src("flux3-action-droid-card", "https://huggingface.co/black-forest-labs/flux-3-action-droid", "hf_black-forest-labs_flux-3-action-droid", "Black Forest Labs",
    "FLUX 3 Action DROID model card, success table")
add("flux-3-action-droid", "flux3-action-droid-card", "other", "base recipe (4 steps with guidance)", PCT, "YES", [("DROID task success", "42.92")])

# ---- Microsoft Fara 1.5 (one table covers the three sizes)
src("fara15-card", "https://huggingface.co/microsoft/Fara1.5-9B", "hf_microsoft_Fara1.5-9B", "Microsoft Research", "Fara 1.5 model card, web-agent benchmarks")
for _rid, _vals in (("fara-15-4b-02563a27", ("80.8", "57.3", "27.4")), ("fara-15-9b-98aec4f3", ("86.6", "63.4", "32.3")),
                    ("fara-15-27b-8c580b31", ("89.3", "72.3", "40.2"))):
    add(_rid, "fara15-card", "image", "default", PCT, "YES",
        [("WebVoyager", _vals[0]), ("Online-Mind2Web", _vals[1]), ("WebTailBench", _vals[2])])

# ---- Kakao Kanana 1.5 (card table 0 = base models, table 1 = instruct models)
src("kanana15-21b-card", "https://huggingface.co/kakaocorp/kanana-1.5-2.1b-base", "hf_kakaocorp_kanana-1.5-2.1b-base", "Kakao", "Kanana 1.5 2.1B model card (base and instruct tables)")
src("kanana15-8b-card", "https://huggingface.co/kakaocorp/kanana-1.5-8b-base", "hf_kakaocorp_kanana-1.5-8b-base", "Kakao", "Kanana 1.5 8B model card (base and instruct tables)")
src("kanana15-157b-card", "https://huggingface.co/kakaocorp/kanana-1.5-15.7b-a3b-instruct", "hf_kakaocorp_kanana-1.5-15.7b-a3b-instruct", "Kakao",
    "Kanana 1.5 15.7B-A3B instruct model card (instruct table)")
src("kanana15-v3b-card", "https://huggingface.co/kakaocorp/kanana-1.5-v-3b-instruct", "hf_kakaocorp_kanana-1.5-v-3b-instruct", "Kakao", "Kanana 1.5 V 3B instruct model card")
add("kanana-15-21b-base-54ed3e64", "kanana15-21b-card", "text", "base", PCT, "YES",
    [("MMLU", "56.30"), ("KMMLU", "45.10"), ("HAERAE", "77.46"), ("HumanEval", "52.44"), ("MBPP", "47.00"), ("GSM8K", "55.95")])
add("kanana-15-21b-instruct-f649eec2", "kanana15-21b-card", "text", "instruct", PCT, "YES",
    [("IFEval", "68.61"), ("HumanEval+", "68.90"), ("MBPP+", "65.08"), ("GSM8K (0-shot)", "81.43"), ("MATH", "60.62"), ("MMLU (0-shot, CoT)", "53.87"), ("KMMLU (0-shot, CoT)", "32.93")])
add("kanana-15-21b-instruct-f649eec2", "kanana15-21b-card", "text", "instruct", "score (1–10)", "YES", [("MT-Bench", "7.01"), ("KoMT-Bench", "6.54")])
add("kanana-15-8b-base-86ed977b", "kanana15-8b-card", "text", "base", PCT, "YES",
    [("MMLU", "64.24"), ("KMMLU", "48.94"), ("HAERAE", "82.77"), ("HumanEval", "61.59"), ("MBPP", "57.80"), ("GSM8K", "63.53")])
add("kanana-15-8b-instruct-99703790", "kanana15-8b-card", "text", "instruct", PCT, "YES",
    [("IFEval", "80.11"), ("HumanEval+", "76.83"), ("MBPP+", "67.99"), ("GSM8K (0-shot)", "87.64"), ("MATH", "67.54"), ("MMLU (0-shot, CoT)", "68.82"), ("KMMLU (0-shot, CoT)", "48.28")])
add("kanana-15-8b-instruct-99703790", "kanana15-8b-card", "text", "instruct", "score (1–10)", "YES", [("MT-Bench", "7.76"), ("KoMT-Bench", "7.63")])
add("kanana-15-157b-a3b-18d06c4b", "kanana15-157b-card", "text", "instruct", PCT, "YES",
    [("IFEval", "73.35"), ("HumanEval+", "79.27"), ("MBPP+", "70.37"), ("GSM8K (0-shot)", "83.02"), ("MATH", "66.42"), ("MMLU (0-shot, CoT)", "68.55"), ("KMMLU (0-shot, CoT)", "48.92")])
add("kanana-15-157b-a3b-18d06c4b", "kanana15-157b-card", "text", "instruct", "score (1–10)", "YES", [("MT-Bench", "7.67"), ("KoMT-Bench", "7.24")])
add("kanana-15-v-3b-e5811ec0", "kanana15-v3b-card", "image", "instruct", PCT, "YES",
    [("MMMU (val)", "43.89"), ("MathVista", "56.00"), ("DocVQA", "93.06"), ("ChartQA", "81.20"), ("OCRBench", "82.50"), ("MMStar", "56.32"), ("AI2D", "74.81")])

# ---- Mistral Ministral 3 (master cards are the API products = Instruct 2512; only the instruct table is used)
src("ministral3-card", "https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512", "hf_mistralai_Ministral-3-8B-Instruct-2512", "Mistral AI",
    "Ministral 3 Instruct 2512 model card, instruct comparison table")
for _rid, _v in (("ministral-3-14b-0047dcfb", ("0.551", "68.5", "0.904", "8.49")), ("ministral-3-8b-fd5ec0ba", ("0.509", "66.8", "0.876", "8.08")),
                 ("ministral-3-3b-53c6b9e3", ("0.305", "56.8", "0.830", "7.83"))):
    add(_rid, "ministral3-card", "text", "Instruct 2512", FRAC, "YES", [("Arena Hard", _v[0]), ("MATH (maj@1)", _v[2])])
    add(_rid, "ministral3-card", "text", "Instruct 2512", PTS, "YES", [("WildBench", _v[1])])
    add(_rid, "ministral3-card", "image", "Instruct 2512", "score (1–10)", "YES", [("MM MT-Bench", _v[3])])

# ---- NAVER HyperCLOVA X SEED
src("hcx-seed-05b-card", "https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-0.5B", "hf_naver-hyperclovax_HyperCLOVAX-SEED-Text-Instruct-0.5B",
    "NAVER Cloud", "HyperCLOVA X SEED Text Instruct 0.5B model card")
add("hyperclova-x-seed-05b-72172208", "hcx-seed-05b-card", "text", "Text-Instruct, 5-shot", FRAC, "YES",
    [("KMMLU (5-shot)", "0.3815"), ("HAE-RAE (5-shot)", "0.5619"), ("CLIcK (5-shot)", "0.4446"), ("KoBEST (5-shot)", "0.6299")])
src("hcx-seed-14b-card", "https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Think-14B", "hf_naver-hyperclovax_HyperCLOVAX-SEED-Think-14B",
    "NAVER Cloud", "HyperCLOVA X SEED 14B Think model card")
add("hyperclova-x-seed-14b-think-602209ad", "hcx-seed-14b-card", "text", "think", FRAC, "YES",
    [("KMMLU", "0.6649"), ("CSAT-ko-2025", "0.7516"), ("KorMedMCQA", "0.6933"), ("HAERAE", "0.8537"), ("CLIcK", "0.7280"),
     ("GSM8K", "0.9553"), ("MATH500", "0.9380"), ("HumanEval", "0.9451"), ("MBPP", "0.8759"), ("Arena-Hard v0.1", "0.5826")])
add("hyperclova-x-seed-14b-think-602209ad", "hcx-seed-14b-card", "text", "think", "score (1–10)", "YES", [("MT-Bench", "8.8313"), ("LogicKor", "8.74")])

# ---- NVIDIA Nemotron 3.5 Content Safety
src("nemo35-safety-card", "https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety", "hf_nvidia_Nemotron-3.5-Content-Safety", "NVIDIA",
    "Nemotron 3.5 Content Safety model card, evaluation tables")
add("nemotron-35-content-safety-0c6eb931", "nemo35-safety-card", "other", "prompt classification", FRAC, "YES",
    [("Aegis 2.0 prompt harmful F1", "0.86"), ("WildGuard prompt harmful F1", "0.85"), ("XSTest prompt harmful F1", "0.85"),
     ("VLGuard prompt harmful F1", "0.90"), ("PolyGuard prompt harmful F1", "0.80")])
add("nemotron-35-content-safety-0c6eb931", "nemo35-safety-card", "other", "response classification", FRAC, "YES",
    [("Aegis 2.0 response harmful F1", "0.85"), ("WildGuard response harmful F1", "0.77")])

# ---- NVIDIA speech
src("parakeet-v3-card", "https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3", "hf_nvidia_parakeet-tdt-0.6b-v3", "NVIDIA", "parakeet-tdt-0.6b-v3 model card, WER tables")
add("parakeet-tdt-06b-v3-7658bc0f", "parakeet-v3-card", "audio", "default decoding", WER, "NO",
    [("FLEURS (25 languages, average)", "11.97"), ("MLS (average)", "7.83"), ("CoVoST (average)", "11.98"), ("Open ASR English set (average of 8)", "6.34"),
     ("LibriSpeech test-clean", "1.93"), ("LibriSpeech test-other", "3.59"), ("AMI", "11.31"), ("Earnings-22", "11.42")])
src("nemotron3-diar-card", "https://huggingface.co/nvidia/Nemotron-3-Diarization", "hf_nvidia_Nemotron-3-Diarization", "NVIDIA",
    "Nemotron 3 Diarization model card, performance evaluation (collar 0 s DIHARD III; 0.25 s CALLHOME-part2)")
add("nemotron-3-diarization", "nemotron3-diar-card", "audio", "offline (30.4 s latency)", "DER %", "NO",
    [("DIHARD III Eval DER (full)", "12.73"), ("CALLHOME-Part2 DER (full)", "9.10")])
add("nemotron-3-diarization", "nemotron3-diar-card", "audio", "low latency (1.04 s, default streaming)", "DER %", "NO",
    [("DIHARD III Eval DER (full)", "13.18"), ("CALLHOME-Part2 DER (full)", "10.29")])

# ---- NVIDIA Nemotron BF16 checkpoints (tables on the BF16 model cards themselves)
src("nemotron3-ultra-bf16-card", "https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16", "hf_nvidia_NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16",
    "NVIDIA", "Nemotron 3 Ultra 550B-A55B BF16 model card, benchmark table")
add("nemotron-3-ultra-550b-a55b-bf16-17196004", "nemotron3-ultra-bf16-card", "text", "default (as reported)", PCT, "YES",
    [("Terminal-Bench 2.1", "56.4"), ("SWE-bench Verified", "70.7"), ("LiveCodeBench v6", "89.0"), ("GPQA (no tools)", "87.0"), ("MMLU-Pro", "86.8"),
     ("HLE (no tools)", "26.7"), ("IFBench (prompt loose)", "81.7"), ("RULER (1M)", "94.7"), ("MMLU-ProX (10-language average)", "83.0")])
src("nemotron35-lightning-bf16-card", "https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16", "hf_nvidia_NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16",
    "NVIDIA", "Nemotron 3.5 Lightning 30B-A3B BF16 model card, benchmark table")
add("nemotron-35-lightning-30b-a3b-bf16-8af433db", "nemotron35-lightning-bf16-card", "text", "default (as reported)", PCT, "YES",
    [("MMLU-Pro", "81.94"), ("GPQA Diamond (no tools)", "75.44"), ("HLE (text-only, no tools)", "11.72"), ("SciCode", "32.60"), ("SWE-bench Verified", "51.56"),
     ("Terminal-Bench 2.1", "24.58"), ("IFBench (loose)", "71.88"), ("AA-LCR", "52.00")])

# ---- Sarvam AI
src("sarvam30b-card", "https://huggingface.co/sarvamai/sarvam-30b", "hf_sarvamai_sarvam-30b", "Sarvam AI", "Sarvam-30B model card, benchmark tables")
add("sarvam-30b-ba107bb6", "sarvam30b-card", "text", "default (as reported)", PCT, "YES",
    [("MATH-500", "97.0"), ("HumanEval", "92.1"), ("LiveCodeBench v6", "70.0"), ("MMLU", "85.1"), ("MMLU-Pro", "80.0"), ("MILU", "76.8"),
     ("GPQA Diamond", "66.5"), ("AIME 2025 (no tools)", "88.3"), ("SWE-bench Verified", "34.0")])
src("sarvam105b-card", "https://huggingface.co/sarvamai/sarvam-105b", "hf_sarvamai_sarvam-105b", "Sarvam AI", "Sarvam-105B model card, benchmark tables")
add("sarvam-105b-9175eb7c", "sarvam105b-card", "text", "default (as reported)", PCT, "YES",
    [("MATH-500", "98.6"), ("LiveCodeBench v6", "71.7"), ("MMLU", "90.6"), ("MMLU-Pro", "81.7"), ("IFEval", "84.8"), ("GPQA Diamond", "78.7"),
     ("AIME 2025 (no tools)", "88.3"), ("SWE-bench Verified (SWE-Agent harness)", "45.0")])

# ---- Zhipu CogView4 (CogView-4 = CogView4-6B, the only released checkpoint)
src("cogview4-card", "https://huggingface.co/zai-org/CogView4-6B", "hf_zai-org_CogView4-6B", "Zhipu AI", "CogView4-6B model card, Model Metrics")
add("cogview-4-57bb01c8", "cogview4-card", "image", "default", PTS, "YES", [("DPG-Bench (overall)", "85.13")])
add("cogview-4-57bb01c8", "cogview4-card", "image", "default", FRAC, "YES", [("GenEval (overall)", "0.73")])

# ---- Fastino GLiNER2.5-Decide (340M)
src("gliner25-decide-card", "https://huggingface.co/fastino/GLiNER2.5-Decide", "hf_fastino_GLiNER2.5-Decide", "Fastino AI",
    "GLiNER2.5-Decide model card, exact-match accuracy on fastino/fast-decisions (17 domains x 300)")
add("gliner-2-5-decide", "gliner25-decide-card", "text", "default", PCT, "YES", [("fast-decisions (exact-match accuracy, 17 domains)", "60.2")])

# ---- Qwen2.5-Omni-7B (first data column = Qwen2.5-Omni-7B)
src("qwen25-omni-card", "https://huggingface.co/Qwen/Qwen2.5-Omni-7B", "hf_Qwen_Qwen2.5-Omni-7B", "Alibaba Qwen", "Qwen2.5-Omni-7B model card, performance tables")
add("qwen25-omni-7b-61cbc63a", "qwen25-omni-card", "audio", "default", WER, "NO",
    [("LibriSpeech test-clean", "1.8"), ("LibriSpeech test-other", "3.4"), ("FLEURS (zh)", "3.0"), ("FLEURS (en)", "4.1"), ("Common Voice 15 (en)", "7.6")])
add("qwen25-omni-7b-61cbc63a", "qwen25-omni-card", "audio", "default", PCT, "YES", [("OmniBench (average)", "56.13")])
add("qwen25-omni-7b-61cbc63a", "qwen25-omni-card", "image", "default", PCT, "YES", [("MMMU (val)", "59.2"), ("MMStar", "64.0"), ("DocVQA (test)", "95.2")])
add("qwen25-omni-7b-61cbc63a", "qwen25-omni-card", "video", "default", PCT, "YES", [("Video-MME (w/o subtitles)", "64.3"), ("MVBench", "70.3")])
add("qwen25-omni-7b-61cbc63a", "qwen25-omni-card", "text", "default", PCT, "YES", [("MMLU-Pro", "47.0"), ("MATH", "71.5"), ("GSM8K", "88.7"), ("HumanEval", "78.7")])

# ---- Cohere North Micro Vision Instruct
src("north-micro-vision-card", "https://huggingface.co/CohereLabs/North-Micro-Vision-Instruct", "hf_CohereLabs_north-micro-vision-instruct", "Cohere Labs",
    "North-Micro-Vision-Instruct model card, benchmark table")
add("north-micro-vision-instruct-d7b57415", "north-micro-vision-card", "image", "default", FRAC, "YES",
    [("MMBench dev EN v1.1", "0.687"), ("MMStar", "0.518"), ("RealWorldQA", "0.622"), ("ChartQA (test)", "0.808"), ("DocVQA (val)", "0.921"),
     ("OCRBench", "0.792"), ("AI2D (test)", "0.775"), ("MMMU (dev/val)", "0.329")])
add("north-micro-vision-instruct-d7b57415", "north-micro-vision-card", "text", "default", FRAC, "YES", [("MMLU (test)", "0.504"), ("IFEval", "0.749")])

# ---- Sarvam AI blogs
src("sarvam-m-blog", "https://www.sarvam.ai/blogs/sarvam-m", "web_sarvam_m", "Sarvam AI", "Sarvam-M blog, benchmark table")
add("sarvam-m-ce03bf75", "sarvam-m-blog", "text", "default (as reported)", FRAC, "YES",
    [("MMLU", "0.87"), ("MMLU-IN", "0.79"), ("ARC-Challenge", "0.95"), ("GPQA Diamond", "0.48"), ("HumanEval", "0.88"), ("LiveCodeBench", "0.44"),
     ("GSM8K", "0.94"), ("MATH", "0.81"), ("IFEval", "0.87"), ("MILU-IN", "0.75")])
add("sarvam-m-ce03bf75", "sarvam-m-blog", "text", "default (as reported)", "score (1–10)", "YES", [("MT-Bench", "8.14")])
src("sarvam-vision21-blog", "https://www.sarvam.ai/blogs/sarvam-vision-2-1", "web_sarvam_vision21", "Sarvam AI", "Sarvam Vision 2.1 blog, olmOCR-Bench / OmniDocBench v1.6 / Sarvam Indic OCR Bench")
add("sarvam-vision-2-1", "sarvam-vision21-blog", "image", "default", PTS, "YES",
    [("olmOCR-Bench (overall)", "87.3"), ("OmniDocBench v1.6 (overall)", "94.97"), ("Sarvam Indic OCR Bench (overall accuracy)", "87.39")])
src("sarvam-vision21-blog-competitor", "https://www.sarvam.ai/blogs/sarvam-vision-2-1", "web_sarvam_vision21", "Sarvam AI (competitor comparison)",
    "Sarvam Vision 2.1 blog: Sarvam's measurement of competing OCR models", kind="competitor", public=False)
add("glm-ocr-16b45691", "sarvam-vision21-blog-competitor", "image", "as run by Sarvam AI", PTS, "YES",
    [("olmOCR-Bench (overall)", "78.9"), ("OmniDocBench v1.6 (overall)", "94.71")])

# ---- MiniMax M2.1 (the headline benchmark chart is an image; the text states VIBE)
src("minimax-m21-news", "https://www.minimax.io/news/minimax-m21", "web_minimax_m21", "MiniMax", "MiniMax M2.1 announcement (text: VIBE average)")
add("minimax-m21-b4b6df50", "minimax-m21-news", "text", "default (as reported)", PTS, "YES", [("VIBE (average)", "88.6")])
src("minimax-m21-card", "https://huggingface.co/MiniMaxAI/MiniMax-M2.1", "hf_MiniMaxAI_MiniMax-M2.1", "MiniMax", "MiniMax-M2.1 model card, benchmark tables")
add("minimax-m21-b4b6df50", "minimax-m21-card", "text", "default (as reported)", PCT, "YES",
    [("SWE-bench Verified", "74.0"), ("SWE-bench Multilingual", "72.5"), ("Terminal-Bench 2.0", "47.9"), ("AIME 2025", "83.0"), ("MMLU-Pro", "88.0"),
     ("GPQA Diamond", "83.0"), ("HLE (no tools)", "22.2"), ("LiveCodeBench", "81.0"), ("IFBench", "70.0")])

# ---- AI Singapore Qwen-SEA-LION v4.5 (Claw-Eval, 107 tasks, pass^3, developer run)
src("sealion-v45-blog", "https://sea-lion.ai/blog/introducing-the-sea-lion-v4-5-suite-agentic-power-and-speed/", "web_sealion_v45", "AI Singapore",
    "SEA-LION v4.5 announcement, Claw-Eval pass^3")
add("qwen-sea-lion-v45-27b-it-a641a40e", "sealion-v45-blog", "text", "thinking enabled", PCT, "YES", [("Claw-Eval (pass^3, 107 tasks)", "45")])
add("qwen-sea-lion-v45-27b-it-a641a40e", "sealion-v45-blog", "text", "thinking disabled", PCT, "YES", [("Claw-Eval (pass^3, 107 tasks)", "40")])

# ---- Mistral Voxtral TTS (human evaluation, developer)
src("voxtral-tts-news", "https://mistral.ai/news/voxtral-tts/", "web_voxtral_tts", "Mistral AI", "Voxtral TTS announcement, human preference evaluation")
add("voxtral-tts-2f3ad2c0", "voxtral-tts-news", "audio", "voice customization", PCT, "YES", [("Human preference win rate vs ElevenLabs (voice customization)", "68.4")])

# ---- ElevenLabs Scribe v2 Realtime (announcement states one aggregate number; benchmark set not named)
src("scribe-v2-rt-blog", "https://elevenlabs.io/blog/introducing-scribe-v2-realtime", "web_scribe_v2_rt", "ElevenLabs", "Scribe v2 Realtime announcement")
add("scribe-v2-realtime-396d95c3", "scribe-v2-rt-blog", "audio", "default", PCT, "YES",
    [("Transcription accuracy across 30 European and Asian languages (benchmark set not named)", "93.5")],
    note="aggregate claim; dataset and metric definition not published")

# ---- Preferred Networks PLaMo 2.2 Prime blog (PFN also re-measures PLaMo 2.1 Prime in the same tables)
src("plamo22-blog", "https://www.preferred.jp/ja/blog/tech/plamo-2-2-prime-release", "web_plamo22_prime", "Preferred Networks",
    "PLaMo 2.2 Prime release blog: Table 1 role-play interview instruction-following, Table 2 MedRECT-ja, Table 3 JMLE (557 questions)")
add("plamo-22-prime-af56bfb2", "plamo22-blog", "text", "default", PCT, "YES",
    [("Role-play interview prompts: instruction-following rate (PFN Table 1)", "23.7"), ("MedRECT-ja: erroneous-sentence extraction accuracy", "57.0"),
     ("JMLE (Japanese medical licensing exam, 557 questions)", "70.7")])
add("plamo-22-prime-af56bfb2", "plamo22-blog", "text", "default", FRAC, "YES", [("MedRECT-ja: error detection F1", "0.661")])
add("plamo-21-prime-cee1a175", "plamo22-blog", "text", "default", PCT, "YES",
    [("Role-play interview prompts: instruction-following rate (PFN Table 1)", "7.03"), ("MedRECT-ja: erroneous-sentence extraction accuracy", "15.8"),
     ("JMLE (Japanese medical licensing exam, 557 questions)", "55.1")])
add("plamo-21-prime-cee1a175", "plamo22-blog", "text", "default", FRAC, "YES", [("MedRECT-ja: error detection F1", "0.556")])

# ---- Apertus v1.5 8B: independent evaluation by DS-NLP Lab (lm-evaluation-harness), no licence stated -> Public=NO
src("dsnlp-apertus15-8b", "https://blog.nlp-lab.ai/2026/07/29/Apertus15Bench.html", "web_dsnlp_apertus15_8b", "DS-NLP Lab",
    "LLM Benchmark Evaluation - Apertus 1.5-8B (swiss-ai/Apertus-v1.5-8B, EleutherAI lm-evaluation-harness)", kind="independent", public=False)
add("apertus-v15-8b-5de97984", "dsnlp-apertus15-8b", "text", "normal mode", PCT, "YES",
    [("GPQA Diamond (0-shot)", "29.8"), ("Global-MMLU (en)", "71.0"), ("IFEval (prompt-strict)", "85.8"), ("MMLU-Pro (5-shot)", "45.9"),
     ("LongBench", "44.2"), ("GSM8K (flexible exact match)", "79.6"), ("MATH-500", "54.0")])
add("apertus-v15-8b-5de97984", "dsnlp-apertus15-8b", "text", "thinking mode", PCT, "YES",
    [("GPQA Diamond (0-shot)", "26.3"), ("IFEval (prompt-strict)", "72.1"), ("GSM8K (flexible exact match)", "85.3"), ("MATH-500", "71.0")])

# ---- Qwen3Guard-Stream (Qwen3Guard Technical Report, arXiv:2510.14276, F1 per benchmark; strict mode shown)
src("qwen3guard-report", "https://arxiv.org/abs/2510.14276", "arxiv_qwen3guard", "Alibaba Qwen", "Qwen3Guard Technical Report (arXiv:2510.14276), F1 tables")
for _rid, _p, _r in (("qwen3guard-stream-0-6b", ("84.9", "87.1", "97.2"), ("84.5", "84.8")),
                     ("qwen3guard-stream-4b", ("86.6", "88.6", "100.0"), ("86.0", "88.5")),
                     ("qwen3guard-stream-8b", ("86.1", "87.5", "99.4"), ("85.9", "87.5"))):
    add(_rid, "qwen3guard-report", "other", "strict mode", "F1 (×100)", "YES",
        [("Aegis 2.0 prompt classification F1", _p[0]), ("WildGuardTest prompt classification F1", _p[1]), ("HarmBench prompt classification F1", _p[2]),
         ("BeaverTails response classification F1", _r[0]), ("XSTest response classification F1", _r[1])])

# ---- Cohere (values transcribed from labelled bar charts published in the official blogs; image saved with SHA-256)
src("north-mini-code-chart", "https://cohere.com/blog/north-mini-code", "../img/cohere_06e7b98d2b53bf7ca8b7dfa53d758991a031c2e5-3140x2400.png", "Cohere",
    "North Mini Code blog, Image 1 (labelled chart; SWE-agent harness for SWE-Bench, ReAct terminal tool for Terminal-Bench v2)")
add("north-mini-code-10-2abc4e72", "north-mini-code-chart", "text", "default (as reported)", PCT, "YES",
    [("Terminal-Bench v2", "36.0"), ("Terminal-Bench Hard", "31.1"), ("SWE-bench Verified", "67.6"), ("SWE-bench Pro", "40.2"), ("SciCode", "38.2"),
     ("LiveCodeBench v6", "70.3")], note="value label transcribed from the official chart")
src("command-a-plus-chart", "https://cohere.com/blog/command-a-plus", "../img/cohere_148eddc43a6f9fc03e0affc9c6d9f2ff395b4c90-3140x1720.png", "Cohere",
    "Introducing Command A+ blog, Image 3 (labelled chart)")
add("command-a-05-2026-fa756fc5", "command-a-plus-chart", "text", "default (as reported)", PCT, "YES",
    [("τ²-Bench Telecom", "85"), ("Terminal-Bench Hard", "25"), ("IFBench", "74"), ("AIME 2025", "90"), ("SciCode", "38")],
    note="value label transcribed from the official chart")

# ---- Meta AudioCraft AudioGen (released checkpoint facebook/audiogen-medium)
src("audiogen-card", "https://github.com/facebookresearch/audiocraft/blob/main/model_cards/AUDIOGEN_MODEL_CARD.md", "web_audiocraft_audiogen_card", "Meta AI",
    "AudioCraft AudioGen model card, AudioCaps evaluation")
add("audiogen-c2c92003", "audiogen-card", "audio", "audiogen-medium", "FAD", "NO", [("AudioCaps Frechet Audio Distance", "1.77")])
add("audiogen-c2c92003", "audiogen-card", "audio", "audiogen-medium", "KL", "NO", [("AudioCaps KL divergence", "1.58")])
add("audiogen-c2c92003", "audiogen-card", "audio", "audiogen-medium", "CLAP score", "YES", [("AudioCaps text consistency (CLAP)", "0.30")])

# ---- Meta Llama Guard 4 12B (PurpleLlama model card)
src("llama-guard4-card", "https://github.com/meta-llama/PurpleLlama/blob/main/Llama-Guard4/12B/MODEL_CARD.md", "web_llama_guard4_card", "Meta",
    "Llama Guard 4 model card, response classification")
add("llama-guard-4-12b-a6c96928", "llama-guard4-card", "image", "default", PCT, "YES",
    [("Internal eval F1 (English)", "61"), ("Internal eval recall (English)", "69"), ("Internal eval F1 (multilingual)", "51"),
     ("Internal eval F1 (single image)", "38"), ("Internal eval F1 (multi-image)", "52")])
add("llama-guard-4-12b-a6c96928", "llama-guard4-card", "image", "default", "FPR %", "NO", [("Internal eval false positive rate (English)", "11")])

# ---- DeepSeek Janus family (developer papers; "Janus" rows in the Janus-Pro paper = Janus-1.3B re-measured by DeepSeek)
src("janus-pro-paper", "https://arxiv.org/abs/2501.17811", "arxiv_janus_pro", "DeepSeek", "Janus-Pro paper (arXiv:2501.17811), Tables 3-5")
for _rid, _u, _g, _d in (("janus-pro-7b-20b552d9", ("87.4", "79.2", "72.1", "62.0", "41.0", "50.0"), "0.80", "84.19"),
                         ("janus-pro-1b-dc7be208", ("86.2", "75.5", "68.3", "59.3", "36.3", "39.8"), "0.73", "82.63"),
                         ("janus-1-3b-2c888a44", ("87.0", "69.4", "63.7", "59.1", "30.5", "34.3"), "0.61", "79.68")):
    add(_rid, "janus-pro-paper", "image", "default", PCT, "YES",
        [("POPE", _u[0]), ("MMBench", _u[1]), ("SEED-Bench", _u[2]), ("GQA", _u[3]), ("MMMU", _u[4]), ("MM-Vet", _u[5])])
    add(_rid, "janus-pro-paper", "image", "default", FRAC, "YES", [("GenEval (overall)", _g)])
    add(_rid, "janus-pro-paper", "image", "default", PTS, "YES", [("DPG-Bench (overall)", _d)])
src("janusflow-paper", "https://arxiv.org/abs/2411.07975", "arxiv_janusflow", "DeepSeek", "JanusFlow paper (arXiv:2411.07975), main results (384 resolution)")
add("janusflow-1-3b-d0249bce", "janusflow-paper", "image", "384 resolution (released model)", PCT, "YES",
    [("POPE", "88.0"), ("MMBench (dev)", "74.9"), ("SEED-Bench", "70.5"), ("GQA", "60.3"), ("MMMU", "29.3"), ("MM-Vet", "30.9"), ("ChartQA", "64.6"), ("TextVQA", "55.5")])
add("janusflow-1-3b-d0249bce", "janusflow-paper", "image", "384 resolution (released model)", FRAC, "YES", [("GenEval (overall)", "0.63")])
add("janusflow-1-3b-d0249bce", "janusflow-paper", "image", "384 resolution (released model)", PTS, "YES", [("DPG-Bench (overall)", "80.09")])
add("janusflow-1-3b-d0249bce", "janusflow-paper", "image", "384 resolution (released model)", "FID", "NO", [("MJHQ-30K FID", "9.51")])

# ---- Meta Llama Prompt Guard 2 (PurpleLlama model card)
src("prompt-guard2-card", "https://github.com/meta-llama/PurpleLlama/blob/main/Llama-Prompt-Guard-2/86M/MODEL_CARD.md", "web_prompt_guard2_86m", "Meta",
    "Llama Prompt Guard 2 model card, detection and AgentDojo tables")
add("llama-prompt-guard-2-86m-40344759", "prompt-guard2-card", "other", "default", FRAC, "YES", [("Jailbreak detection AUC (English)", ".998"), ("Jailbreak detection AUC (multilingual)", ".995")])
add("llama-prompt-guard-2-86m-40344759", "prompt-guard2-card", "other", "default", PCT, "YES", [("Recall at 1% FPR (English)", "97.5"), ("AgentDojo attack prevention rate at 3% utility reduction", "81.2")])
add("llama-prompt-guard-2-22m-4036c92b", "prompt-guard2-card", "other", "default", FRAC, "YES", [("Jailbreak detection AUC (English)", ".995"), ("Jailbreak detection AUC (multilingual)", ".942")])
add("llama-prompt-guard-2-22m-4036c92b", "prompt-guard2-card", "other", "default", PCT, "YES", [("Recall at 1% FPR (English)", "88.7"), ("AgentDojo attack prevention rate at 3% utility reduction", "78.4")])

# ---- Meta SAM (paper; "SAM" = the released default ViT-H model)
src("sam-paper", "https://arxiv.org/abs/2304.02643", "arxiv_sam", "Meta AI", "Segment Anything paper (arXiv:2304.02643), zero-shot transfer tables")
add("segment-anything-model-sam-64ee423f", "sam-paper", "image", "ViT-H (paper default), zero-shot", FRAC, "YES", [("BSDS500 edge detection ODS", ".768")])
add("segment-anything-model-sam-64ee423f", "sam-paper", "image", "ViT-H (paper default), zero-shot", PTS, "YES",
    [("LVIS v1 object proposals mask AR@1000", "59.3"), ("COCO instance segmentation mask AP", "46.5"), ("LVIS v1 instance segmentation mask AP", "44.7")])

# ---- Meta BlenderBot 3 175B (paper human evaluations)
src("bb3-paper", "https://arxiv.org/abs/2208.03188", "arxiv_blenderbot3", "Meta AI", "BlenderBot 3 paper (arXiv:2208.03188), human evaluations (Tables 4-5)")
add("blenderbot-3-175b-fb95bf1d", "bb3-paper", "text", "human evaluation", PCT, "YES",
    [("Human eval: consistent responses", "85.8"), ("Human eval: knowledgeable & engaging", "39.0"), ("Topical-prompt eval: good response rate", "64.8")])
add("blenderbot-3-175b-fb95bf1d", "bb3-paper", "text", "human evaluation", "rating (1–5)", "YES", [("Human eval: final conversation rating", "4.45")])

# ---- Wan-AI (developer papers)
src("wan-animate-paper", "https://arxiv.org/abs/2509.14055", "arxiv_wan_animate", "Alibaba Wan team", "Wan-Animate paper (arXiv:2509.14055), quantitative comparison")
add("wan-22-animate-14b-10b1612a", "wan-animate-paper", "video", "body animation", "FVD", "NO", [("Body animation FVD", "118.65")])
add("wan-22-animate-14b-10b1612a", "wan-animate-paper", "video", "body animation", "SSIM", "YES", [("Body animation SSIM", "0.813")])
add("wan-22-animate-14b-10b1612a", "wan-animate-paper", "video", "portrait animation", "FVD", "NO", [("Portrait animation FVD", "94.65")])
src("wan-s2v-paper", "https://arxiv.org/abs/2508.18621", "arxiv_wan_s2v", "Alibaba Wan team", "Wan-S2V paper (arXiv:2508.18621), quantitative comparison (Ours)")
add("wan-22-s2v-14b-6675fc11", "wan-s2v-paper", "video", "default", "FID", "NO", [("FID", "15.66")])
add("wan-22-s2v-14b-6675fc11", "wan-s2v-paper", "video", "default", "FVD", "NO", [("FVD", "129.57")])
add("wan-22-s2v-14b-6675fc11", "wan-s2v-paper", "video", "default", "Sync-C", "YES", [("Lip sync confidence (Sync-C)", "4.51")])
add("wan-22-s2v-14b-6675fc11", "wan-s2v-paper", "video", "default", "CSIM", "YES", [("Identity consistency (CSIM)", "0.677")])

# ---- Zhipu GLM-OCR / GLM-ASR-2512 (developer documentation)
src("glm-ocr-docs", "https://docs.z.ai/guides/vlm/glm-ocr", "web_glm_ocr", "Zhipu AI", "GLM-OCR documentation overview")
add("glm-ocr-16b45691", "glm-ocr-docs", "image", "default", PTS, "YES", [("OmniDocBench v1.5 (overall)", "94.62")])
src("glm-asr-docs", "https://docs.z.ai/guides/audio/glm-asr-2512", "web_glm_asr", "Zhipu AI", "GLM-ASR-2512 documentation overview")
add("glm-asr-2512-965d77ed", "glm-asr-docs", "audio", "default", "CER (fraction)", "NO", [("Character error rate (evaluation set not named)", "0.0717")],
    note="aggregate claim; evaluation set not published")

# ---- Mistral OCR 4 (= mistral-ocr-4-0 per Mistral changelog)
src("mistral-ocr4-news", "https://mistral.ai/news/ocr-4/", "web_mistral_ocr4", "Mistral AI", "Mistral OCR 4 announcement, Benchmarks section")
add("mistral-ocr-40-82177582", "mistral-ocr4-news", "image", "default", PTS, "YES", [("OlmOCR-Bench (overall)", "85.20"), ("OmniDocBench (overall)", "93.07")])
add("mistral-ocr-40-82177582", "mistral-ocr4-news", "image", "default", PCT, "YES",
    [("Human preference win rate vs leading OCR systems (average, annotators engaged by Mistral)", "72")])

# ---- Amazon Nova Canvas / Nova Reel (Amazon Nova technical report, arXiv:2506.12103)
src("nova-report", "https://arxiv.org/abs/2506.12103", "arxiv_nova", "Amazon", "The Amazon Nova Family of Models: Technical Report and Model Card (Tables 9-11)")
add("amazon-nova-canvas-3c05ef45", "nova-report", "image", "default", FRAC, "YES", [("TIFA", "0.897")])
add("amazon-nova-canvas-3c05ef45", "nova-report", "image", "default", "ImageReward", "YES", [("ImageReward", "1.250")])
add("amazon-nova-canvas-3c05ef45", "nova-report", "image", "default", PCT, "YES",
    [("Human A/B win rate vs DALL·E 3 (overall image quality)", "54.5"), ("Human A/B win rate vs Imagen 3 (overall image quality)", "48.2")])
add("amazon-nova-reel-1b171943", "nova-report", "video", "default", PCT, "YES",
    [("Human pairwise win rate vs Runway Gen-3 Alpha (video quality)", "56.4"), ("Human pairwise win rate vs Runway Gen-3 Alpha (video consistency)", "67.0"),
     ("Human pairwise win rate vs Luma 1.6 (video quality)", "51.1"), ("Human pairwise win rate vs Luma 1.6 (video consistency)", "74.7")])

# ---- Amazon Nova Premier (AWS News Blog benchmark table image)
src("nova-premier-chart", "https://aws.amazon.com/blogs/aws/amazon-nova-premier-our-most-capable-model-for-complex-tasks-and-teacher-for-model-distillation/",
    "../img/aws_nova_premier_benchmarks.png", "Amazon", "Amazon Nova Premier launch blog, benchmark table image")
add("amazon-nova-premier-e1ebcb91", "nova-premier-chart", "text", "default (as reported)", PCT, "YES",
    [("MMLU", "87.4"), ("GPQA Diamond", "57.1"), ("AIME 2025", "16.0"), ("MATH-500", "82.0"), ("BigCodeBench Hard", "28.1"), ("IFEval", "91.5"),
     ("SWE-bench Verified (internal agentic scaffold)", "42.4")], note="value transcribed from the official table image")
add("amazon-nova-premier-e1ebcb91", "nova-premier-chart", "image", "default (as reported)", PCT, "YES",
    [("MMMU", "68.0"), ("OCRBench v2", "56.9"), ("EgoSchema", "73.8")], note="value transcribed from the official table image")


def st(rid, status, en, ru, checked):
    """Explicit stage-2 status for a model without (or beyond) numeric rows."""
    STATUS[rid] = {"status": status, "found_en": en, "found_ru": ru, "checked": list(checked)}


# ---- ELYZA (official note.com blog, result tables/charts as images)
src("elyza3-tasks-chart", "https://note.com/elyza/n/n360b6084fdbd", "../img/elyza_1719299913752-UqlWMbyL2a.png", "ELYZA",
    "Llama-3-ELYZA-JP release blog: ELYZA Tasks 100 automatic evaluation (GPT-4o judge) chart")
src("elyza3-mtbench-table", "https://note.com/elyza/n/n360b6084fdbd", "../img/elyza_1719294712227-BCATpw7rg0.png", "ELYZA",
    "Llama-3-ELYZA-JP release blog: Japanese MT-Bench results table (all 8 categories)")
for rid, tasks, mt in (("llama-3-elyza-jp-70b-525ffabd", "4.070", "9.08"), ("llama-3-elyza-jp-8b-d9dab6d1", "3.655", "7.78")):
    add(rid, "elyza3-tasks-chart", "text", "GPT-4o automatic judge", "points (1–5)", "YES", [("ELYZA Tasks 100", tasks)],
        note="value transcribed from the official chart image")
    add(rid, "elyza3-mtbench-table", "text", "Japanese MT-Bench repository defaults", "points (1–10)", "YES", [("Japanese MT-Bench (average)", mt)],
        note="value transcribed from the official table image")
st("llama-31-elyza-jp-70b-f11a923e", "no_published_numerical_evaluation",
   "The launch press release describes improvements qualitatively but publishes no benchmark numbers for Llama-3.1-ELYZA-JP-70B; "
   "the Llama-3-ELYZA-JP scores belong to the previous version and are not transferred.",
   "Пресс-релиз описывает улучшения словами, числовых результатов для Llama-3.1-ELYZA-JP-70B нет; оценки Llama-3-ELYZA-JP относятся к прошлой версии и не переносятся.",
   ["https://prtimes.jp/main/html/rd/p/000000052.000047565.html", "https://note.com/elyza/n/n360b6084fdbd"])

# ---- Google Gemini 3.5 Transcribe (Google blog; AA-measured WER is excluded — AA is not republishable)
src("gemini35-transcribe-blog", "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5-transcribe/",
    "web_gemini35_transcribe", "Google", "Gemini 3.5 Transcribe launch blog (FLEURS, set of top languages and locales)")
add("gemini-35-transcribe-4a2a6a85", "gemini35-transcribe-blog", "audio", "non-streaming", WER, "NO", [("FLEURS (top languages and locales)", "5.04")])
# changelog 2026-08-26: gemini-3.5-transcribe is non-streaming; streaming is the separate gemini-3.5-transcribe-live model
add("gemini-35-transcribe-live-fd2bb178", "gemini35-transcribe-blog", "audio", "streaming (Live API)", WER, "NO", [("FLEURS (top languages and locales)", "5.50")])

# ---- Google Gemini audio: DeepMind "Evals & Methodology" PDFs. Third-party results reproduced there keep the
# third party as evaluator; Hume AI sells TTS (competitor → rating-ineligible), Voice Arena has no published
# results licence (research-only). Artificial Analysis values are excluded everywhere (not republishable).
src("g31live-evals", "https://deepmind.google/models/evals-methodology/gemini-3-1-flash-live/", "web_dm_evals_gemini-3-1-flash-live", "Google",
    "Gemini 3.1 Flash Live evals & methodology (ComplexFuncBench Audio run by Google on the Live API)")
add("gemini-31-flash-live-preview-027a2841", "g31live-evals", "audio", "thinking = high", PCT, "YES", [("ComplexFuncBench Audio", "90.8")])
src("g31live-scale", "https://deepmind.google/models/evals-methodology/gemini-3-1-flash-live/", "web_dm_evals_gemini-3-1-flash-live", "Scale AI",
    "Audio MultiChallenge (run externally by Scale AI, as reproduced by Google)", kind="independent", public=False)
add("gemini-31-flash-live-preview-027a2841", "g31live-scale", "audio", "thinking = high", PCT, "YES", [("Audio MultiChallenge (overall)", "36.1")])
add("gemini-31-flash-live-preview-027a2841", "g31live-scale", "audio", "thinking = minimal", PCT, "YES", [("Audio MultiChallenge (overall)", "26.8")])
src("g38live-tau3", "https://deepmind.google/models/evals-methodology/gemini-3-8-live/", "../img/g38live_p4_0.png", "Google",
    "Gemini 3.8 Live evals & methodology: τ³-Banking chart (run by Google with the Gemini API)")
add("gemini-38-live-extended-thinking-4ab0af55", "g38live-tau3", "audio", "thinking = high", PCT, "YES", [("τ³-Bench Banking", "35.1")],
    note="value transcribed from the official chart image")
add("gemini-31-flash-live-preview-027a2841", "g38live-tau3", "audio", "thinking = high", PCT, "YES", [("τ³-Bench Banking", "11.3")],
    note="value transcribed from the official chart image")
src("g38tts-hume", "https://deepmind.google/models/evals-methodology/gemini-3-8-tts/", "../img/g38tts_p2_0.png", "Hume AI",
    "Hume AI Text-to-Speech Quality Benchmark, as reproduced in the Gemini 3.8 TTS evals PDF", kind="competitor", public=False)
for rid, ov, hv, ms, stc in (("gemini-3-8-flash-tts", "0.920", "4.58", "4.14", "4.34"), ("gemini-3-8-flash-lite-tts", "0.914", "4.51", "4.10", "4.32"),
                             ("gemini-31-flash-tts-preview-54794803", "0.783", "3.95", "3.60", "4.31"), ("eleven-v3-42cde628", "0.706", "5.00", "3.85", "3.89"),
                             ("eleven-v3-conversational-15ae3db9", "0.769", "4.97", None, "3.97")):
    add(rid, "g38tts-hume", "audio", "default", "points (0–1)", "YES", [("Hume TTS Quality: overall (reliability × expressiveness)", ov)],
        note="value transcribed from the official table image")
    pairs = [("Hume TTS Quality: human-like variation", hv), ("Hume TTS Quality: style tag control (single tag)", stc)]
    if ms:
        pairs.append(("Hume TTS Quality: multispeaker", ms))
    add(rid, "g38tts-hume", "audio", "default", "points (1–5)", "YES", pairs, note="value transcribed from the official table image")
src("g38tts-voicearena", "https://deepmind.google/models/evals-methodology/gemini-3-8-tts/", "../img/g38tts_p3_0.png", "Voice Arena",
    "Voice Arena TTS leaderboard (crowdsourced blind pairwise Elo), as reproduced in the Gemini 3.8 TTS evals PDF", kind="independent", public=False)
LANGS = ("English", "Japanese", "Brazilian Portuguese", "Vietnamese", "Arabic MSA", "Hindi", "Mexican Spanish")
for rid, vals in (("gemini-3-8-flash-tts", "1061 1232 1104 1135 1204 1106 1152"), ("gemini-3-8-flash-lite-tts", "1087 1152 1134 1156 1181 1076 1146"),
                  ("gemini-31-flash-tts-preview-54794803", "1051 1148 1094 1099 1135 1086 1092"), ("eleven-v3-42cde628", "986 1048 1040 1043 1020 1052 1015")):
    add(rid, "g38tts-voicearena", "audio", "default", "Elo", "YES", [("Voice Arena TTS Elo (%s)" % l, v) for l, v in zip(LANGS, vals.split())],
        note="value transcribed from the official table image; leaderboard as of September 2026")
st("gemini-38-live-a959d0c7", "independent_nonpublic",
   "Google's evals PDF shows Gemini 3.8 Live only in ServiceNow EVA-Bench (scatter without value labels) and Artificial Analysis charts "
   "(not republishable); no transcribable developer-run number for this exact model.",
   "В PDF Google модель Gemini 3.8 Live есть только на диаграмме ServiceNow EVA-Bench без подписанных значений и в графиках Artificial Analysis (републикация запрещена); "
   "числа собственного прогона разработчика для этой версии нет.",
   ["https://deepmind.google/models/evals-methodology/gemini-3-8-live/", "https://deepmind.google/models/model-cards/gemini-3-8-audio/"])

# ---- Google Veo 3.1 Lite / Lyria 3.5 (DeepMind model cards)
src("veo31lite-card", "https://deepmind.google/models/model-cards/veo-3-1-lite/", "web_dm_card_veo-3-1-lite", "Google DeepMind",
    "Veo 3.1 Lite model card, Evaluation results (human side-by-side vs Veo 3.1 Fast)")
add("veo-31-lite-a2e55fd8", "veo31lite-card", "video", "text-to-video, 1000 prompts", PCT, "YES", [("Human side-by-side win rate vs Veo 3.1 Fast (T2V, overall)", "54.6")])
add("veo-31-lite-a2e55fd8", "veo31lite-card", "video", "image-to-video, 646 prompts", PCT, "YES", [("Human side-by-side win rate vs Veo 3.1 Fast (I2V, overall)", "47.2")])
st("lyria-35-86454fa7", "no_published_numerical_evaluation",
   "The Lyria 3.5 model card describes human and automated evaluations only qualitatively (improvement over Lyria 2); no numeric result is published.",
   "Карточка Lyria 3.5 описывает оценки людьми и автоматические только словами (лучше Lyria 2); чисел не опубликовано.",
   ["https://deepmind.google/models/model-cards/lyria-3-5/", "https://ai.google.dev/gemini-api/docs/changelog"])

# ---- ElevenLabs Scribe v2 (launch blog FLEURS chart; accuracy = 100 − WER as published)
src("scribe-v2-chart", "https://elevenlabs.io/blog/introducing-scribe-v2", "../img/scribe_v2_fleurs.png", "ElevenLabs",
    "Introducing Scribe v2: FLEURS results across 30 European and Asian languages (chart)")
add("scribe-v2-e1191f04", "scribe-v2-chart", "audio", "batch transcription", "% (accuracy = 100 − WER)", "YES",
    [("FLEURS accuracy (30 European and Asian languages)", "95.7")], note="value transcribed from the official chart image")
src("scribe-v2-chart-competitor", "https://elevenlabs.io/blog/introducing-scribe-v2", "../img/scribe_v2_fleurs.png", "ElevenLabs",
    "Introducing Scribe v2: FLEURS chart — competitor model measured by ElevenLabs", kind="competitor", public=False)
add("gpt-4o-transcribe-c0eb2c95", "scribe-v2-chart-competitor", "audio", "as run by ElevenLabs", "% (accuracy = 100 − WER)", "YES",
    [("FLEURS accuracy (30 European and Asian languages)", "94.1")], note="value transcribed from a competitor's chart image")

# ---- ElevenLabs Scribe v2 Medical launch blog (public clinical benchmarks, ElevenLabs runs)
src("scribe-med-blog", "https://elevenlabs.io/blog/scribe-v2-medical-is-now-available-to-everyone", "web_scribe_v2_medical", "ElevenLabs",
    "Scribe v2 Medical launch blog: MedDictate, MedTerm and Eka Medical ASR tables")
src("scribe-med-blog-competitor", "https://elevenlabs.io/blog/scribe-v2-medical-is-now-available-to-everyone", "web_scribe_v2_medical", "ElevenLabs",
    "Scribe v2 Medical launch blog: competitor model measured by ElevenLabs", kind="competitor", public=False)
for rid, srck, dic, term in (("scribe-v2-medical-ee4cce87", "scribe-med-blog", ("3.0", "8.3", "7.2", "4.9"), ("77.7", "10.4", "6.50", "6.02")),
                             ("scribe-v2-e1191f04", "scribe-med-blog", ("5.0", "10.7", "11.7", "7.6"), ("77.1", "10.7", "7.35", "7.04")),
                             ("gpt-transcribe-71b7a2b4", "scribe-med-blog-competitor", ("3.9", "7.8", "9.6", "5.9"), ("74.0", "12.3", "13.90", "13.20"))):
    add(rid, srck, "audio", "batch", WER, "NO", [("MedDictate (EN)", dic[0]), ("MedDictate (FR)", dic[1]), ("MedDictate (DE)", dic[2]),
                                                  ("MedDictate (overall)", dic[3]), ("MedTerm Term-WER", term[1]),
                                                  ("Eka Medical ASR semWER", term[2]), ("Eka Medical ASR kwWER", term[3])])
    add(rid, srck, "audio", "batch", PCT, "YES", [("MedTerm term recall", term[0])])

# ---- Stability AI Stable Audio 3 technical report (arXiv:2605.17991v1); OVL/REL/MUS = listener ratings (1–5)
src("sa3-report", "https://arxiv.org/abs/2605.17991", "arxiv_stable_audio_3", "Stability AI",
    "Stable Audio 3 technical report, Tables 3 (SDD music, 120 s) and 5 (BBC Sound Effects, 5 s)")
for rid, fad, clap, ovl, rel, mus in (("stable-audio-3-medium-1d67b621", "0.107", "0.390", "4.20", "4.25", "4.15"),
                                      ("stable-audio-3-small-music-2632c9a7", "0.145", "0.393", "3.20", "3.60", "3.15")):
    add(rid, "sa3-report", "audio", "instrumental music, 120 s", "FAD", "NO", [("SDD music FAD (LAION-CLAP)", fad)])
    add(rid, "sa3-report", "audio", "instrumental music, 120 s", "CLAP score", "YES", [("SDD music CLAP score", clap)])
    add(rid, "sa3-report", "audio", "instrumental music, 120 s", "points (1–5)", "YES",
        [("SDD music listening test OVL", ovl), ("SDD music listening test REL", rel), ("SDD music listening test MUS", mus)])
for rid, fad, clap, ovl, rel in (("stable-audio-3-medium-1d67b621", "0.369", "0.369", "3.65", "3.95"),
                                 ("stable-audio-3-small-sfx-a685bbca", "0.395", "0.351", "3.35", "3.25")):
    add(rid, "sa3-report", "audio", "sound effects, 5 s", "FAD", "NO", [("BBC Sound Effects FAD (LAION-CLAP)", fad)])
    add(rid, "sa3-report", "audio", "sound effects, 5 s", "CLAP score", "YES", [("BBC Sound Effects CLAP score", clap)])
    add(rid, "sa3-report", "audio", "sound effects, 5 s", "points (1–5)", "YES",
        [("BBC Sound Effects listening test OVL", ovl), ("BBC Sound Effects listening test REL", rel)])

# ---- Tencent AuK / AuK-Flash (identical performance.png in both HF repos; bars identified by legend colour:
# AuK = dark blue, AuK-Flash = light blue). Enhancement/separation panels carry two unlabelled metrics per model → not transcribed.
src("auk-chart", "https://huggingface.co/tencent/AuK", "../img/auk_performance.png", "Tencent", "AuK model card, assets/performance.png (panels a–b)")
for rid, wer, sim, dsd, emr, seb, ming in (("auk-5a8f1067", "2.65", "0.795", "82.49", "12.44", "49.73", "88.54"),
                                           ("auk-flash-14134b6b", "2.85", "0.790", "80.60", "13.85", "46.66", "87.55")):
    note = "value transcribed from the official chart image (bar identified by legend colour)"
    add(rid, "auk-chart", "audio", "speech generation", WER, "NO", [("Seed-TTS-Eval WER", wer)], note=note)
    add(rid, "auk-chart", "audio", "speech generation", "speaker similarity (0–1)", "YES", [("Seed-TTS-Eval SIM", sim)], note=note)
    add(rid, "auk-chart", "audio", "speech generation", "points (as published)", "YES",
        [("InstructTTSEval DSD", dsd), ("MMAE-Speech EMR", emr), ("SpeechEditBench", seb), ("Ming-Freeform-Audio-Edit", ming)], note=note)

# ---- Mistral Voxtral Transcribe 2 launch post, per-language FLEURS bar chart (labelled values)
FL9 = ("Italian", "Spanish", "English", "German", "Portuguese", "French", "Russian", "Dutch", "Chinese")
src("vt2-fleurs", "https://mistral.ai/news/voxtral-transcribe-2/", "../img/vt2_97f4a4ee-7448-4a2f-889e-17409821e503_ZCsc9n.png", "Mistral AI",
    "Voxtral Transcribe 2 launch post: Transcription FLEURS per-language WER chart")
src("vt2-fleurs-competitor", "https://mistral.ai/news/voxtral-transcribe-2/", "../img/vt2_97f4a4ee-7448-4a2f-889e-17409821e503_ZCsc9n.png", "Mistral AI",
    "Voxtral Transcribe 2 launch post: FLEURS chart — competitor models measured by Mistral", kind="competitor", public=False)
for rid, srck, vals in (("voxtral-mini-transcribe-2-bc935e7f", "vt2-fleurs", "2.2 2.6 3.3 3.5 3.6 4.3 4.8 4.8 7.3"),
                        ("scribe-v2-e1191f04", "vt2-fleurs-competitor", "1.5 2.8 2.9 3.6 4.1 4.2 5.3 4.2 7.3"),
                        ("gpt-4o-mini-transcribe-2101891e", "vt2-fleurs-competitor", "2.8 3.4 3.7 4.0 5.2 5.9 5.3 6.0 8.8")):
    add(rid, srck, "audio", "batch", WER, "NO", [("FLEURS (%s)" % l, v) for l, v in zip(FL9, vals.split())],
        note="value transcribed from the official chart image")

# ---- Cohere Transcribe Arabic (Cohere Labs HF release blog)
src("cohere-ar-blog", "https://huggingface.co/blog/CohereLabs/cohere-transcribe-arabic-07-2026-release", "hf_blog_cohere_transcribe_arabic",
    "Cohere Labs", "Meet Cohere Transcribe Arabic: public benchmark and dialect tables")
add("cohere-transcribe-arabic-07-2026-a7a6d392", "cohere-ar-blog", "audio", "default", WER, "NO",
    [("Arabic public benchmarks (average WER)", "25.87"), ("SADA", "37.47"), ("Common Voice (Arabic)", "5.82"), ("MASC (clean)", "15.54"),
     ("MASC (noisy)", "27.07"), ("MGB-2", "15.54"), ("Casablanca", "49.71"), ("Code-switched Arabic–English", "27.84"), ("Gulf", "24.36"),
     ("Najdi", "26.18"), ("Hijazi", "16.24"), ("Egyptian", "19.16"), ("Levantine", "39.78"), ("North African", "36.94")])

# ---- OpenAI audio: launch posts (openai.com, read in a browser 2026-09-27) state only relative gains in the text
# ("+15.2% on Big Bench Audio vs GPT-Realtime-1.5", "+30 pp Full Duplex Bench vs GPT-Realtime-2.1"); chart values are not
# present in the page text/DOM, so no absolute number for these exact versions is recorded.
_OA = ["https://developers.openai.com/api/docs/changelog", "https://openai.com/index/advancing-voice-intelligence-with-new-models-in-the-api/",
       "https://openai.com/index/introducing-gpt-live-1-in-the-api/", "https://developers.openai.com/blog/updates-audio-models",
       "https://openai.com/index/introducing-our-next-generation-audio-models/"]
_OA_EN = ("OpenAI publishes only relative improvements in text (and charts whose values are not in the page text) for this exact model; "
          "no absolute numeric result could be verified.")
_OA_RU = ("OpenAI публикует для этой версии только относительные улучшения в тексте (значения графиков в тексте страницы отсутствуют); "
          "абсолютного проверяемого числа не найдено.")
for rid in ("gpt-live-transcribe-57aa6ad5", "gpt-realtime-21-f3f0c1d7", "gpt-realtime-21-mini-8ff2e8cc",
            "gpt-realtime-whisper-f5e0ce27", "gpt-live-1-60f09da9"):
    st(rid, "exact_version_not_found", _OA_EN, _OA_RU, _OA)

# ---- ElevenLabs products without published numbers
st("eleven-music-d60ed664", "no_published_numerical_evaluation", "The Eleven Music launch post contains demos and features but no benchmark or evaluation number.",
   "Пост о запуске Eleven Music содержит демо и возможности, но ни одного числа оценки.", ["https://elevenlabs.io/blog/eleven-music-is-here"])
st("eleven-dubbing-v2-bf9fe195", "no_published_numerical_evaluation", "The Dubbing v2 launch post describes quality qualitatively; the only figure is a customer production-time case study, not an evaluation.",
   "Пост о Dubbing v2 описывает качество словами; единственное число — кейс клиента о времени производства, а не оценка.",
   ["https://elevenlabs.io/blog/introducing-dubbing-v2"])

# ---- Qwen3.8-LiveTranslate (Qwen blog, FLEURS 19 languages / 70 directions chart; blog is JS-rendered, text read in a browser)
src("qwen38-lt-fleurs", "https://qwen.ai/blog?id=qwen3.8-livetranslate", "../img/qwen38_lt_fleurs.png", "Alibaba Qwen",
    "Qwen3.8-LiveTranslate blog: FLEURS real-time interpretation chart (70 directions)")
src("qwen38-lt-fleurs-competitor", "https://qwen.ai/blog?id=qwen3.8-livetranslate", "../img/qwen38_lt_fleurs.png", "Alibaba Qwen",
    "Qwen3.8-LiveTranslate blog: FLEURS chart — competitor systems measured by Qwen", kind="competitor", public=False)
_n = "value transcribed from the official chart image"
add("qwen38-livetranslate-c09db33d", "qwen38-lt-fleurs", "audio", "real-time interpretation, 70 directions", "points (0–100)", "YES", [("FLEURS xCOMET-XXL", "85.7")], note=_n)
add("qwen38-livetranslate-c09db33d", "qwen38-lt-fleurs", "audio", "real-time interpretation, 70 directions", "seconds", "NO", [("FLEURS average lagging (LAAL)", "2.3")], note=_n)
add("qwen38-livetranslate-c09db33d", "qwen38-lt-fleurs", "audio", "real-time interpretation, 70 directions", WER, "NO", [("FLEURS ASR WER", "6.6")], note=_n)
add("qwen38-livetranslate-c09db33d", "qwen38-lt-fleurs", "audio", "real-time interpretation, 70 directions", "points (1–5)", "YES", [("FLEURS UTMOS", "4.0")], note=_n)
add("gpt-realtime-translate-228d1eb0", "qwen38-lt-fleurs-competitor", "audio", "as run by Qwen, 70 directions", "points (0–100)", "YES", [("FLEURS xCOMET-XXL", "65.2")], note=_n)
add("gpt-realtime-translate-228d1eb0", "qwen38-lt-fleurs-competitor", "audio", "as run by Qwen, 70 directions", "seconds", "NO", [("FLEURS average lagging (LAAL)", "3.1")], note=_n)
add("gpt-realtime-translate-228d1eb0", "qwen38-lt-fleurs-competitor", "audio", "as run by Qwen, 70 directions", "points (1–5)", "YES", [("FLEURS UTMOS", "3.4")], note=_n)
st("yandex-speech-tts-live", "no_published_numerical_evaluation",
   "Yandex AI Studio documentation and SpeechKit release notes describe the realtime TTS without any quality metric (MOS or other).",
   "Документация Yandex AI Studio и история изменений SpeechKit описывают realtime-синтез без метрик качества (MOS и др.).",
   ["https://aistudio.yandex.ru/ru/docs/speechkit/tts/api/tts-realtime", "https://aistudio.yandex.ru/docs/ru/speechkit/release-notes-tts.html"])

# ---- Google DiffusionGemma 26B A4B IT (HF model card, instruction-tuned, Entropy Bound sampler)
src("diffusiongemma-card", "https://huggingface.co/google/diffusiongemma-26B-A4B-it", "hf_google_diffusiongemma", "Google DeepMind",
    "DiffusionGemma 26B A4B IT model card, benchmark table")
_cfg = "instruction-tuned, Entropy Bound sampler"
add("diffusiongemma-26b-a4b-it-428856e3", "diffusiongemma-card", "text", _cfg, PCT, "YES",
    [("MMLU-Pro", "77.6"), ("AIME 2026 (no tools)", "69.1"), ("LiveCodeBench v6", "69.1"), ("GPQA Diamond", "73.2"), ("τ²-Bench (average over 3)", "56.2"),
     ("Humanity's Last Exam (no tools)", "11.0"), ("Humanity's Last Exam (with search)", "11.9"), ("BIG-Bench Extra Hard", "47.6"), ("MMMLU", "81.5"),
     ("MRCR v2 8-needle 128k (average)", "32.0")])
add("diffusiongemma-26b-a4b-it-428856e3", "diffusiongemma-card", "text", _cfg, "Elo", "YES", [("Codeforces Elo", "1429")])
add("diffusiongemma-26b-a4b-it-428856e3", "diffusiongemma-card", "image", _cfg, PCT, "YES",
    [("MMMU-Pro", "54.3"), ("MATH-Vision", "70.5"), ("MedXPertQA MM", "49.0")])
add("diffusiongemma-26b-a4b-it-428856e3", "diffusiongemma-card", "image", _cfg, "edit distance", "NO", [("OmniDocBench 1.5 (average edit distance)", "0.319")])

# ---- Mistral Leanstral 1.5 (launch post, text values)
src("leanstral15-news", "https://mistral.ai/news/leanstral-1-5/", "web_leanstral15", "Mistral AI", "Leanstral 1.5: Proof Abundance for All (launch post)")
add("leanstral-15-411a728b", "leanstral15-news", "text", "default (as reported)", PCT, "YES",
    [("miniF2F (test)", "100"), ("miniF2F (validation)", "100"), ("FATE-H", "87"), ("FATE-X", "34"), ("FLTEval pass@1", "28.9"), ("FLTEval pass@8", "43.2")])
add("leanstral-15-411a728b", "leanstral15-news", "text", "pass@8, 4M-token budget per attempt", "problems solved (of 672)", "YES", [("PutnamBench", "587")])

# ---- Mistral Small 4 (119B-2603) HF model card charts (internal benchmarks; instruct vs reasoning bars)
src("ms4-chart-internal", "https://huggingface.co/mistralai/Mistral-Small-4-119B-2603", "../img/ms4_image2.png", "Mistral AI",
    "Mistral Small 4 model card: performance comparison across internal models (instruct / reasoning)")
src("ms4-chart-reasoning", "https://huggingface.co/mistralai/Mistral-Small-4-119B-2603", "../img/ms4_image3.png", "Mistral AI",
    "Mistral Small 4 model card: reasoning (high) comparison chart")
_n = "value transcribed from the official chart image"
add("mistral-small-4-10c41350", "ms4-chart-internal", "text", "instruct", PCT, "YES",
    [("GPQA Diamond", "59.1"), ("MMLU-Pro", "73.5"), ("IFBench (AllenAI)", "35.7"), ("Arena Hard", "55.8")], note=_n)
add("mistral-small-4-10c41350", "ms4-chart-internal", "text", "reasoning", PCT, "YES",
    [("GPQA Diamond", "71.2"), ("MMLU-Pro", "78"), ("IFBench (AllenAI)", "48"), ("Arena Hard", "58.3")], note=_n)
add("mistral-small-4-10c41350", "ms4-chart-internal", "image", "instruct", PCT, "YES", [("MMMU-Pro", "46.3")], note=_n)
add("mistral-small-4-10c41350", "ms4-chart-internal", "image", "reasoning", PCT, "YES", [("MMMU-Pro", "60")], note=_n)
add("mistral-small-4-10c41350", "ms4-chart-reasoning", "text", "reasoning = high", PCT, "YES",
    [("AA-LCR (run by Mistral)", "71.2"), ("AIME 2025", "83.8"), ("COLLIE", "62.9"), ("LiveCodeBench", "63.6")], note=_n)

# ---- Mistral products without transcribable numbers
st("mistral-ocr-41-0dd2b9e7", "no_published_numerical_evaluation",
   "Mistral's changelog announces OCR 4.1 (mistral-ocr-4-1) without benchmark numbers; the OCR 4 launch figures belong to mistral-ocr-4-0 and are not transferred.",
   "Changelog Mistral объявляет OCR 4.1 без чисел; результаты запуска OCR 4 относятся к mistral-ocr-4-0 и не переносятся.",
   ["https://docs.mistral.ai/resources/changelogs", "https://mistral.ai/news/ocr-4/"])
st("codestral-embed-79e6c4d8", "no_published_numerical_evaluation",
   "The Codestral Embed launch post shows results only as charts without value labels (retrieval nDCG@10 vs storage cost, per-category bars); no number can be transcribed without estimation.",
   "Пост о Codestral Embed показывает результаты только графиками без подписанных значений; перенести число без оценки на глаз нельзя.",
   ["https://mistral.ai/news/codestral-embed/"])
st("mistral-moderation-2-74c8e4cc", "no_published_numerical_evaluation",
   "The Mistral Moderation 26.03 model page and the changelog publish no evaluation numbers.",
   "Страница модели Mistral Moderation 26.03 и changelog не публикуют чисел оценки.",
   ["https://docs.mistral.ai/models/mistral-moderation-26-03", "https://docs.mistral.ai/resources/changelogs"])
st("flux11-pro-ultra-ff451a32", "no_published_numerical_evaluation",
   "The FLUX1.1 [pro] Ultra launch post gives only a speed comparison ('over 2.5x faster'); quality Elo figures circulating online are Artificial Analysis values for FLUX1.1 [pro] (another version, not republishable).",
   "Пост о FLUX1.1 [pro] Ultra даёт лишь сравнение скорости; Elo из интернета — значения Artificial Analysis для FLUX1.1 [pro] (другая версия, републикация запрещена).",
   ["https://bfl.ai/blog/24-11-06-ultra"])

st("stable-diffusion-35-medium-2ff6dd26", "no_published_numerical_evaluation",
   "Stability AI's SD 3.5 announcement shows SD 3.5 Medium only in an Elo bar chart without value labels (prompt adherence / aesthetic quality); the gated HF card has no evaluation table.",
   "Анонс SD 3.5 показывает SD 3.5 Medium только на графике Elo без подписанных значений; закрытая карточка HF таблицы оценок не содержит.",
   ["https://stability.ai/news-updates/introducing-stable-diffusion-3-5", "https://huggingface.co/stabilityai/stable-diffusion-3.5-medium"])
st("apertus-v15-70b-344f8097", "no_published_numerical_evaluation",
   "The Apertus 1.5 release article and model card defer benchmark results to a technical report 'in the coming weeks'; no numeric evaluation of the 70B model is published yet (the DS-NLP Lab study covers only the 8B).",
   "Статья о выпуске Apertus 1.5 и карточка откладывают результаты до технического отчёта; числовых оценок 70B пока нет (исследование DS-NLP Lab касается только 8B).",
   ["https://www.apertus-ai.org/articles/2026-07-apertus-1-5/", "https://huggingface.co/swiss-ai/Apertus-v1.5-70B", "https://blog.nlp-lab.ai/2026/07/29/Apertus15Bench.html"])
for rid, name in (("claude-1-109a2931", "Claude 1"), ("claude-instant-1-08b06766", "Claude Instant 1")):
    st(rid, "exact_version_not_found",
       "The 'Introducing Claude' announcement publishes no benchmark numbers for %s; figures in later Anthropic documents are for Claude 1.3 / Claude Instant 1.1 (later versions) and are not transferred." % name,
       "Анонс «Introducing Claude» не содержит чисел для %s; значения в поздних документах Anthropic относятся к Claude 1.3 / Claude Instant 1.1 (другие версии) и не переносятся." % name,
       ["https://www.anthropic.com/news/introducing-claude", "https://www-cdn.anthropic.com/5c49cc247484cecf107c699baf29250302e5da70/claude-2-model-card.pdf"])

# ---- Amazon Nova 2 Lite (AWS News Blog benchmark table image)
src("nova2lite-chart", "https://aws.amazon.com/blogs/aws/introducing-amazon-nova-2-lite-a-fast-cost-effective-reasoning-model/",
    "../img/aws_nova2lite_bench.png", "Amazon", "Introducing Amazon Nova 2 Lite (AWS News Blog), benchmark table image")
_n = "value transcribed from the official table image"
add("amazon-nova-2-lite-43b653c0", "nova2lite-chart", "text", "default (as reported)", PCT, "YES",
    [("MMLU-Pro", "80.9"), ("GPQA Diamond", "79.6"), ("AIME 2025", "91.0"), ("IFBench", "70.8"), ("MultiChallenge", "76.6"), ("LongCodeBench 1M", "84.0"),
     ("τ²-Bench Telecom", "76.0"), ("τ²-Bench Retail (verified)", "76.5"), ("τ²-Bench Airline (verified)", "64.8"), ("BFCL v4 overall (FC)", "60.3"),
     ("Scale MCP Atlas", "24.6"), ("SWE-bench Verified", "64.5"), ("Terminal-Bench 1 (overall)", "32.5"), ("LiveCodeBench", "71.0")], note=_n)
add("amazon-nova-2-lite-43b653c0", "nova2lite-chart", "image", "default (as reported)", PCT, "YES",
    [("MMMU-Pro", "61.8"), ("OCRBench v2", "56.1"), ("RealKIE", "62.1"), ("ScreenSpot", "83.3")], note=_n)
add("amazon-nova-2-lite-43b653c0", "nova2lite-chart", "video", "default (as reported)", PCT, "YES", [("QVHighlights", "77.2")], note=_n)
st("amazon-nova-2-pro-preview-807c8417", "exact_version_not_found",
   "Amazon's Nova 2 technical report (assets.amazon.science PDF) returns 404/download-only to automated retrieval and could not be read; "
   "the AWS launch pages give no absolute numbers for Nova 2 Pro (Preview). Numbers quoted by third-party sites were not verified at the source.",
   "Технический отчёт Nova 2 (PDF на assets.amazon.science) недоступен для автоматического чтения (404/только скачивание); страницы AWS не дают абсолютных чисел для Nova 2 Pro (Preview). "
   "Числа со сторонних сайтов по первоисточнику не проверены.",
   ["https://assets.amazon.science/c5/3d/84514a224666b5be6de4b43ef4aa/nova-2-0-technical-report2.pdf",
    "https://aws.amazon.com/about-aws/whats-new/2025/12/nova-2-foundation-models-amazon-bedrock"])

# ---- Wan-Animate-2 paper (arXiv:2608.06009, linked from the Wan2.2-Animate-2-14B card): blind user study, Figure 6 (labelled)
src("wan-animate2-study", "https://arxiv.org/abs/2608.06009", "../img/wan_animate2_userstudy.png", "Alibaba Wan team",
    "Wan-Animate-2 paper, Figure 6 blind user study (share of pairwise comparisons preferring Wan-Animate-2)")
_n = "value transcribed from the official figure image; 'same' votes excluded from this share"
for other, vals in (("Wan-Animate", ("78.5", "82.3", "71.6", "74.2", "68.3", "65.9")),
                    ("Dreamina", ("32.3", "32.5", "30.5", "36.5", "28.3", "37.2")),
                    ("Kling MotionControl", ("25.9", "27.4", "23.8", "28.5", "23.8", "25.6"))):
    add("wan-22-animate-2-14b-d11d7821", "wan-animate2-study", "video", "character animation", PCT, "YES",
        [("User study vs %s: preferred (%s)" % (other, dim), v) for dim, v in
         zip(("overall", "visual quality", "dynamic quality", "identity preservation", "motion accuracy", "expression accuracy"), vals)], note=_n)
st("wan-22-ti2v-5b-ffe796a2", "exact_version_not_found",
   "The Wan2.2 card's Wan-Bench 2.0 comparison is for the flagship Wan2.2 A14B models; TI2V-5B has only efficiency figures, no quality evaluation of this exact model.",
   "Сравнение Wan-Bench 2.0 в карточке Wan2.2 относится к флагманским моделям A14B; для TI2V-5B есть только данные о скорости, оценки качества этой версии нет.",
   ["https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B", "https://github.com/Wan-Video/Wan2.2"])
st("wan-dancer-14b-60691663", "no_published_numerical_evaluation",
   "The Wan-Dancer-14B model card contains usage examples and demo videos but no evaluation numbers.",
   "Карточка Wan-Dancer-14B содержит примеры и демо-видео, но не числа оценки.", ["https://huggingface.co/Wan-AI/Wan-Dancer-14B"])

_RW = ["https://runway.com/changelog", "https://runway.com/research"]
for rid, name in (("runway-act-two-fe953e93", "Act-Two"), ("runway-aleph-2-ba558832", "Aleph 2.0"), ("runway-gen-4-image-turbo-c1622317", "Gen-4 Image Turbo")):
    st(rid, "no_published_numerical_evaluation",
       "Runway's changelog and research pages describe %s qualitatively; no evaluation number is published for this model." % name,
       "Changelog и исследовательские страницы Runway описывают %s словами; числовых оценок этой модели нет." % name, _RW)
st("cogvideox-3-a2fe3208", "no_published_numerical_evaluation",
   "The Z.ai CogVideoX-3 documentation shows qualitative examples only; VBench figures online are for CogVideoX-5B/1.5 (other versions).",
   "Документация Z.ai по CogVideoX-3 содержит только примеры; значения VBench в сети относятся к CogVideoX-5B/1.5 (другие версии).",
   ["https://docs.z.ai/guides/video/cogvideox-3", "https://docs.z.ai/release-notes/new-released"])
st("flux-video-upscale-e29d2e3c", "no_published_numerical_evaluation",
   "The FLUX Video Upscale launch post and documentation give specifications and pricing but no quality evaluation numbers.",
   "Пост о запуске и документация FLUX Video Upscale дают характеристики и цены, но не числа оценки качества.",
   ["https://bfl.ai/blog/flux-video-upscale", "https://docs.bfl.ml/flux_tools/flux_video_upscale"])

# ---- Tencent HY-Motion 1.0 (arXiv:2512.23464, Tables 1–2: 2000+ prompts, human ratings 1–5, SSAE video-VLM check)
src("hy-motion-paper", "https://arxiv.org/abs/2512.23464", "arxiv_hy_motion", "Tencent Hunyuan", "HY-Motion 1.0 paper, Tables 1–2")
add("hy-motion-10-009f04c5", "hy-motion-paper", "other", "text-to-motion, 2000+ prompts", "points (1–5)", "YES",
    [("Human rating: instruction following (average over 6 categories)", "3.24"), ("Human rating: motion quality (average over 6 categories)", "3.43")])
add("hy-motion-10-009f04c5", "hy-motion-paper", "other", "text-to-motion, 2000+ prompts", PCT, "YES", [("SSAE (Structured Semantic Alignment Evaluation)", "78.6")])
st("flux-3-action-so101", "no_published_numerical_evaluation",
   "BFL's FLUX 3 Action post reports RoboLab-120 success only for the DROID fine-tune; the SO-101 policy is shown in demo videos without a success rate.",
   "Пост BFL о FLUX 3 Action приводит успех RoboLab-120 только для версии DROID; политика SO-101 показана в демо-видео без процента успеха.",
   ["https://huggingface.co/blog/black-forest-labs/flux-3-action", "https://huggingface.co/black-forest-labs/flux-3-action-so101"])
st("hunyuan3d-2mini-turbo-c17df073", "exact_version_not_found",
   "The Hunyuan3D-2 repository's evaluation table covers Hunyuan3D 2.0; no numeric evaluation is published for the 2mini Turbo checkpoint.",
   "Таблица оценок в репозитории Hunyuan3D-2 относится к Hunyuan3D 2.0; для 2mini Turbo числовых оценок нет.",
   ["https://github.com/Tencent-Hunyuan/Hunyuan3D-2", "https://huggingface.co/tencent/Hunyuan3D-2mini"])

# ---- AlphaFold 3: independent academic benchmarks as summarised by EMBL-EBI training (primary papers cited; licence not open → research-only)
src("foldbench-af3", "https://www.ebi.ac.uk/training/online/courses/alphafold/alphafold-3-and-alphafold-server/introducing-alphafold-3/how-have-alphafold-3s-predictions-been-validated/",
    "web_ebi_af3_validation", "FoldBench (Xu et al., 2025)", "FoldBench low-homology all-atom benchmark, as reported by EMBL-EBI", kind="independent", public=False)
add("alphafold-3-9a669b23", "foldbench-af3", "other", "default AF3 inference", PCT, "YES",
    [("FoldBench protein–ligand success rate (overall)", "64.9"), ("FoldBench protein–ligand success rate (unseen proteins)", "69.0"),
     ("FoldBench protein–ligand success rate (unseen ligands)", "64.3")])
src("covalid-af3", "https://www.ebi.ac.uk/training/online/courses/alphafold/alphafold-3-and-alphafold-server/introducing-alphafold-3/how-have-alphafold-3s-predictions-been-validated/",
    "web_ebi_af3_validation", "COValid (Shamir & London, 2025)", "COValid covalent-binder benchmark, as reported by EMBL-EBI", kind="independent", public=False)
add("alphafold-3-9a669b23", "covalid-af3", "other", "default AF3 inference", PCT, "YES", [("COValid covalent active vs decoy classification (average AUC)", "98.3")])

# ---- AI Singapore Nemotron SEA-LION v4.8 (technical report arXiv:2609.18310v2, Table 5 SEA-HELM, gathered 2026-09-15)
src("sealion48-report", "https://arxiv.org/abs/2609.18310", "arxiv_sealion48", "AI Singapore", "SEA-LION-v4.8 technical report, Table 5 (SEA-HELM by language)")
SEAL = ("overall SEA average", "Burmese", "Filipino", "Indonesian", "Malay", "Tamil", "Thai", "Vietnamese")
for rid, vals in (("nemotron-sea-lion-v48-30b-a3b-2d708c4d", "51.57 10.61 61.82 65.87 62.09 33.14 62.60 64.86"),
                  ("nemotron-sea-lion-v48-120b-a12b-9efd2066", "63.44 31.35 71.01 73.10 73.25 56.35 68.66 70.36")):
    add(rid, "sealion48-report", "text", "post-trained release", "points (0–100)", "YES",
        [("SEA-HELM (%s)" % l, v) for l, v in zip(SEAL, vals.split())], note="SEA-HELM is maintained by AI Singapore (the developer)")

# ---- YandexGPT 5 Lite 8B Instruct (HF card benchmark table image; MMLU 5-shot, others 0-shot)
src("yandexgpt5lite-table", "https://huggingface.co/yandex/YandexGPT-5-Lite-8B-instruct", "../img/yandexgpt5lite_bench.png", "Yandex",
    "YandexGPT-5-Lite-8B-instruct model card, benchmark table image")
add("yandexgpt-5-lite-8b-instruct-1be85824", "yandexgpt5lite-table", "text", "MMLU 5-shot, other benchmarks 0-shot", PCT, "YES",
    [("MMLU", "75.8"), ("MMLU (Russian, Yandex)", "70.0"), ("MMLU-Pro", "52.2"), ("RuWikiFacts (Yandex)", "59.7"), ("RuFacts (Yandex)", "80.5"),
     ("RuCulture (Yandex)", "57.6"), ("TriviaQA", "68.1"), ("IFEval (Russian)", "76.9"), ("IFEval", "72.6"), ("GSM8K", "87.9"),
     ("GSM8K (Russian, Yandex)", "82.0"), ("MATH", "71.5"), ("SchoolMath 5–9 (Yandex)", "89.0"), ("SchoolMath 10–11 (Yandex)", "73.0"),
     ("HumanEval", "71.8"), ("MBPP", "68.5"), ("BFCL", "56.0"), ("Crowd v2 (Yandex)", "73.1"), ("DROP", "65.1"), ("DROP (Russian, Yandex)", "58.0"),
     ("LogicBench", "74.9"), ("QuALITY", "79.3"), ("Closed-QA Bookworm 7.5k (Yandex)", "88.5"), ("Closed-QA Bookworm 24k (Yandex)", "88.4"),
     ("Extract from recipes 32k (Yandex)", "94.7")], note="value transcribed from the official table image")

# ---- Cohere Labs North Small Translate (technical report arXiv:2609.13916, Tables 1–2; GEMBA judged by GPT-5.6-Sol per report)
src("nst-report", "https://arxiv.org/abs/2609.13916", "arxiv_north_small_translate", "Cohere Labs",
    "North Small Translate technical report (Cohere CAT+), summary and WMT26 regional tables")
for rid, vals in (("north-small-translate-10-edfeef02", ("83.6", "80.6", "89.7", "48.9", "93.7", "82.0", "86.1")),
                  ("command-a-05-2026-fa756fc5", ("76.5", "81.0", "68.7", "30.5", "73.7", "76.0", "77.4"))):
    add(rid, "nst-report", "text", "standard (non-agentic) translation", "points (0–100)", "YES",
        [("WMT26 GEMBA (all languages)", vals[0]), ("WMT24++ xCOMET-XL", vals[1]), ("Terminology accuracy", vals[2]),
         ("Long-context translation (xCOMET-XL per paragraph)", vals[3]), ("Structured translation", vals[4]),
         ("WMT26 GEMBA (Europe)", vals[5]), ("WMT26 GEMBA (Middle East + Asia)", vals[6])])
st("fugu-ultra-30efec3e", "identity_ambiguous",
   "Sakana publishes Fugu Ultra results for a moving multi-agent system (v1.0, v1.1, v2.0 with a changing model pool); the catalogue record does not pin a version, so no score is attached.",
   "Sakana публикует результаты Fugu Ultra для меняющейся мультиагентной системы (v1.0, v1.1, v2.0 с разным пулом моделей); запись каталога не фиксирует версию, поэтому оценка не привязывается.",
   ["https://sakana.ai/fugu/", "https://sakana.ai/fugu-release/"])
st("solar-pro-2-31b-b20a98f3", "no_published_numerical_evaluation",
   "Upstage's Solar Pro 2 launch post and press release name benchmarks (MMLU-Pro, Ko-MMLU, Hae-Rae, Ko-Arena-Hard-Auto) but give no numbers in the text; the charts are not machine-readable.",
   "Пост и пресс-релиз Upstage о Solar Pro 2 называют бенчмарки, но не дают чисел в тексте; графики не читаются как данные.",
   ["https://www.upstage.ai/blog/en/solar-pro-2-launch", "https://www.upstage.ai/news/solar-pro-2"])
st("magenticbrain-7f41d924", "no_published_numerical_evaluation",
   "The MagenticBrain model card and the MagenticLite research blog report no capability benchmark numbers for MagenticBrain "
   "(safety evaluation only qualitatively: 'comparable to or better than Qwen3-14B').",
   "Карточка MagenticBrain и блог MagenticLite не публикуют чисел по возможностям MagenticBrain (безопасность — только словами).",
   ["https://huggingface.co/microsoft/MagenticBrain",
    "https://www.microsoft.com/en-us/research/blog/magenticlite-magenticbrain-fara1-5-an-agentic-experience-optimized-for-small-models/"])
st("tsuzumi-2-6d1154e9", "no_published_numerical_evaluation",
   "NTT's tsuzumi 2 release shows benchmark results only as bar charts without value labels (llm-jp-eval, M-IFEval-Ja, AnswerCarefully); no number can be transcribed without estimation.",
   "Релиз NTT tsuzumi 2 показывает результаты только графиками без подписанных значений; перенести число без оценки на глаз нельзя.",
   ["https://group.ntt/en/newsrelease/2025/10/20/251020a.html", "https://www.rd.ntt/e/research/LLM_tsuzumi.html"])

# ---- Preferred Networks PLaMo 2.0 Prime release blog (31B chart; PLaMo 1.0 Prime shown as the previous commercial model)
src("plamo20-chart", "https://www.preferred.jp/ja/blog/tech/plamo-2-prime-release", "../img/plamo20_4498fa8d6e8ad31a7be4abdf1a220e3f.png",
    "Preferred Networks", "PLaMo 2.0 Prime release blog: Jaster 4-shot, M-IFEval Japanese, pfgen (temperature 0.0) chart")
_n = "value transcribed from the official chart image"
for rid, vals in (("plamo-20-prime-31b-cd7f441e", ("0.665", "0.677", "0.890")), ("plamo-prime-088809ae", ("0.620", "0.342", "0.846"))):
    add(rid, "plamo20-chart", "text", "temperature 0.0", "score (0–1)", "YES",
        [("Jaster 4-shot (Japanese knowledge)", vals[0]), ("M-IFEval Japanese", vals[1]), ("pfgen (Japanese generation)", vals[2])], note=_n)

# ---- NAVER HyperCLOVA X SEED Text Instruct 1.5B (HF card table; 5-shot accuracy 0–1)
src("hcx15-card", "https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B", "hf_hcx_seed_15b_html", "NAVER Cloud",
    "HyperCLOVAX-SEED-Text-Instruct-1.5B model card, benchmark table")
add("hyperclova-x-seed-15b-e8631b7d", "hcx15-card", "text", "5-shot", FRAC, "YES",
    [("KMMLU (5-shot)", "0.3933"), ("HAE-RAE (5-shot)", "0.5674"), ("CLIcK (5-shot)", "0.4947"), ("KoBEST (5-shot)", "0.6490")])

# ---- remaining explicit statuses (checked 2026-09-27/28)
st("plamo-translate-aba1ee70", "no_published_numerical_evaluation",
   "PFN's PLaMo Translate announcement and technical blog compare translations with qualitative examples only; no metric (BLEU/COMET) is published.",
   "Анонс и технический блог PFN о PLaMo Translate сравнивают переводы только примерами; метрик (BLEU/COMET) нет.",
   ["https://www.preferred.jp/en/news/pr20250527", "https://tech.preferred.jp/ja/blog/plamo-translate/"])
st("plamo-2-8b-3bef329a", "exact_version_not_found",
   "The gated pfnet/plamo-2-8b card shows no evaluation table; PFN charts report 'PLaMo 2.0 8B' / 'PLaMo 2.1 (8B)' post-trained variants, not this base checkpoint.",
   "Закрытая карточка pfnet/plamo-2-8b не содержит таблицы оценок; графики PFN относятся к дообученным вариантам PLaMo 2.0/2.1 8B, а не к этой базовой версии.",
   ["https://huggingface.co/pfnet/plamo-2-8b", "https://www.preferred.jp/ja/blog/tech/plamo-2-prime-release"])
_HELM = ["https://crfm.stanford.edu/helm/classic/latest/", "https://www.ai21.com/blog/introducing-j2/", "https://www.ai21.com/blog/announcing-ai21-studio-and-jurassic-1/"]
for rid, name, helm, renamed in (("jurassic-1-jumbo-3bcc324f", "Jurassic-1 Jumbo", "J1-Jumbo v1 (178B)", None),
                                 ("jurassic-2-ultra-2edbabd7", "Jurassic-2 Ultra", "Jurassic-2 Jumbo", "Ultra"),
                                 ("jurassic-2-mid-d07628b1", "Jurassic-2 Mid", "Jurassic-2 Grande", "Mid"),
                                 ("jurassic-2-light-275da84e", "Jurassic-2 Light", "Jurassic-2 Large", "Light")):
    st(rid, "independent_nonpublic",
       "%s was evaluated by Stanford HELM Classic as %s%s; HELM results carry no open republication licence, so AIpedia records the fact without scores. AI21's own posts give no numbers for this exact model." % (
           name, helm, " (later renamed %s)" % renamed if renamed else ""),
       "%s оценена в Stanford HELM Classic под названием %s%s; результаты HELM не имеют открытой лицензии на републикацию, поэтому AIpedia фиксирует факт без баллов. Посты AI21 чисел для этой версии не дают." % (
           name, helm, " (позже переименована в %s)" % renamed if renamed else ""),
       _HELM)
_FAM = "identity_ambiguous"
st("exaone-40-9d0b00ae", _FAM, "LG publishes EXAONE 4.0 results separately for 32B and 1.2B; the catalogue record names the family, so no score is attached.",
   "LG публикует результаты EXAONE 4.0 отдельно для 32B и 1.2B; запись каталога — семейство, оценка не привязывается.",
   ["https://www.lgresearch.ai/blog/view?seq=576", "https://huggingface.co/LGAI-EXAONE/EXAONE-4.0-32B"])
st("nllb-200-ffaac194", _FAM, "NLLB-200 results are reported for several checkpoints (3.3B, 1.3B, distilled 600M, 54.5B MoE); the record does not pin one.",
   "Результаты NLLB-200 опубликованы для нескольких чекпойнтов (3.3B, 1.3B, 600M, 54.5B MoE); запись не фиксирует один.",
   ["https://arxiv.org/abs/2207.04672", "https://github.com/facebookresearch/fairseq/tree/nllb"])
for rid, name in (("sam-2-330bb60e", "SAM 2"), ("sam-2-1-064c4826", "SAM 2.1")):
    st(rid, _FAM, "%s is released as four checkpoints (tiny, small, base+, large) with separate results; the record names the release, so no score is attached." % name,
       "%s выпущен четырьмя чекпойнтами (tiny, small, base+, large) с отдельными результатами; запись называет выпуск, оценка не привязывается." % name,
       ["https://github.com/facebookresearch/sam2/blob/main/RELEASE_NOTES.md", "https://arxiv.org/abs/2408.00714"])
st("musicgen-9783d116", _FAM, "MusicGen results are reported per size (300M, 1.5B, 3.3B, melody); the record names the family.",
   "Результаты MusicGen опубликованы по размерам (300M, 1.5B, 3.3B, melody); запись — семейство.", ["https://arxiv.org/abs/2306.05284"])
st("hyperclova-x-seed-3b-3e1c5933", _FAM, "The record points to HyperCLOVAX-SEED-Vision-Instruct-3B while being named 'HyperCLOVA X SEED 3B'; text and vision 3B variants exist, so the exact checkpoint is not certain.",
   "Запись указывает на HyperCLOVAX-SEED-Vision-Instruct-3B, но названа 'HyperCLOVA X SEED 3B'; существуют текстовый и vision-варианты 3B, точный чекпойнт не определён.",
   ["https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Vision-Instruct-3B"])
st("palm-2-d8ca3c69", _FAM, "The PaLM 2 technical report gives results per size (PaLM 2-S, -M, -L); the record names the family.",
   "Технический отчёт PaLM 2 даёт результаты по размерам (S, M, L); запись — семейство.", ["https://arxiv.org/abs/2305.10403"])
st("gemini-10-nano-f0ed7097", _FAM, "The Gemini 1.0 report gives separate results for Nano-1 (1.8B) and Nano-2 (3.25B); the record names 'Gemini 1.0 Nano'.",
   "Отчёт Gemini 1.0 даёт отдельные результаты для Nano-1 (1.8B) и Nano-2 (3.25B); запись — 'Gemini 1.0 Nano'.", ["https://arxiv.org/abs/2312.11805"])
st("qwen38-24t-a95b-fc5f809f", "exact_version_not_found",
   "The Qwen3.8 repository table reports Qwen3.8-Max (the API-derived version), not the open 2.4T-A95B checkpoint; no score is transferred.",
   "Таблица репозитория Qwen3.8 относится к Qwen3.8-Max (API-версия), а не к открытому чекпойнту 2.4T-A95B; оценка не переносится.",
   ["https://github.com/QwenLM/Qwen3.8"])
st("kimi-k3-max-8906b43f", "not_applicable",
   "Kimi K3 (max) is a reasoning-effort configuration of Kimi K3, not a separate model; evaluations belong to the parent record with Configuration 'max'.",
   "Kimi K3 (max) — конфигурация уровня рассуждения Kimi K3, а не отдельная модель; оценки относятся к родительской записи с Configuration 'max'.",
   ["https://github.com/MoonshotAI/Kimi-K3"])
st("longcat-2-5-preview", "no_published_numerical_evaluation",
   "The LongCat changelog lists LongCat-2.5-Preview without benchmark numbers; published LongCat results are for other releases.",
   "Changelog LongCat указывает LongCat-2.5-Preview без чисел; опубликованные результаты относятся к другим выпускам.",
   ["https://longcat.chat/platform/docs/ChangeLog.html"])

# ======================================================================= final Local pass (2026-09-28)

# ---- OpenAI audio launch posts: charts rendered in a browser; values from SVG labels / bar aria-labels (captures saved)
src("oai-nextgen-fleurs", "https://openai.com/index/introducing-our-next-generation-audio-models/", "browser_openai_nextgen_audio", "OpenAI",
    "Introducing next-generation audio models in the API: FLEURS WER by language chart (bar aria-labels)")
_OAI = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "artifacts", "eval-audit-2026-09-27", "stage2", "pages",
                                    "browser_openai_nextgen_audio.raw"), encoding="utf-8").read())["values"]
_LANG = {"en": "English", "es": "Spanish", "pt": "Portuguese", "fr": "French", "cmn": "Mandarin Chinese", "de": "German", "ja": "Japanese",
         "id": "Indonesian", "ru": "Russian", "it": "Italian", "tr": "Turkish", "ar": "Arabic", "hi": "Hindi", "ko": "Korean", "nl": "Dutch",
         "pl": "Polish", "vi": "Vietnamese", "uk": "Ukrainian", "sv": "Swedish", "da": "Danish", "nb": "Norwegian Bokmål", "th": "Thai",
         "ro": "Romanian", "ms": "Malay", "bn": "Bengali", "mr": "Marathi", "ta": "Tamil", "te": "Telugu", "gu": "Gujarati", "ur": "Urdu",
         "ml": "Malayalam", "kn": "Kannada", "sw": "Swahili"}
for rid, key in (("gpt-4o-transcribe-c0eb2c95", "gpt-4o-transcribe"), ("gpt-4o-mini-transcribe-2101891e", "gpt-4o-mini-transcribe")):
    add(rid, "oai-nextgen-fleurs", "audio", "original release snapshot (launch post)", WER, "NO",
        [("FLEURS (%s)" % _LANG[code], value) for code, value in _OAI[key].items()], note="value read from the chart's bar label")
src("oai-gpt-live-1", "https://openai.com/index/introducing-gpt-live-1-in-the-api/", "browser_openai_gpt_live_1", "OpenAI",
    "Build more natural voice experiences with GPT-Live-1 in the API: evaluation charts (SVG labels)")
_n = "value read from the chart's SVG label; Artificial Analysis chart on the same page excluded"
add("gpt-live-1-60f09da9", "oai-gpt-live-1", "audio", "GPT-Live backend: GPT-6 Astra (medium)", PCT, "YES",
    [("Tau3 (Voice) pass@1", "86.2"), ("Tau Banking (Voice) knowledge pass@1", "32.0"), ("Full Duplex Bench v3 tool calling pass@1", "87.0"),
     ("Full Duplex Bench v3 response quality", "90.0")], note=_n)
add("gpt-live-1-60f09da9", "oai-gpt-live-1", "audio", "default", PCT, "YES", [("Full Duplex Bench v1.5 interactivity (average)", "80.10")], note=_n)
add("gpt-live-1-60f09da9", "oai-gpt-live-1", "audio", "default", "seconds", "NO", [("Full Duplex Bench v1 turn-taking latency", "0.798")], note=_n)
add("gpt-realtime-21-f3f0c1d7", "oai-gpt-live-1", "audio", "as run by OpenAI (effort not stated)", PCT, "YES",
    [("Tau3 (Voice) pass@1", "45.7"), ("Tau Banking (Voice) knowledge pass@1", "12.4"), ("Full Duplex Bench v3 tool calling pass@1", "60.0"),
     ("Full Duplex Bench v3 response quality", "88.0"), ("Full Duplex Bench v1.5 interactivity (average)", "45.4")], note=_n)
add("gpt-realtime-21-f3f0c1d7", "oai-gpt-live-1", "audio", "as run by OpenAI (effort not stated)", "seconds", "NO",
    [("Full Duplex Bench v1 turn-taking latency", "1.41")], note=_n)

# ---- AI21 Jurassic-1 white paper, Table 6 (zero-shot, formats of Brown et al. 2020; AI21 lm-evaluation suite)
src("j1-whitepaper", "https://uploads-ssl.webflow.com/60fd4503684b466578c0d307/61138924626a6981ee09caf6_jurassic_tech_paper.pdf",
    "pdf_jurassic1_whitepaper", "AI21 Labs", "Jurassic-1: Technical Details and Evaluation (white paper), Table 6 zero-shot results")
add("jurassic-1-jumbo-3bcc324f", "j1-whitepaper", "text", "zero-shot", PCT, "YES",
    [("ARC-Challenge", "48.1"), ("ARC-Easy", "67.1"), ("BoolQ", "73.5"), ("HellaSwag", "79.3"), ("PIQA", "81.4"), ("RACE-high", "45.9"),
     ("RACE-middle", "56.6"), ("RTE", "62.8"), ("StoryCloze", "83.1"), ("WinoGrande", "68.9"), ("Zero-shot average (10 tasks)", "66.7")])

# ---- Preferred Networks PLaMo 2 technical report (arXiv:2509.04897v1), base-model tables (column "PLaMo 2 8B")
src("plamo2-report", "https://arxiv.org/abs/2509.04897", "arxiv_plamo2", "Preferred Networks", "PLaMo 2 Technical Report, Tables 1–4 (base models)")
add("plamo-2-8b-3bef329a", "plamo2-report", "text", "base model", FRAC, "YES",
    [("JMMLU (5-shot)", "0.572"), ("MMLU (5-shot)", "0.573"), ("JHumanEval (0-shot pass@1)", "0.463"), ("HumanEval+ (0-shot pass@1)", "0.463"),
     ("JMMLU Japanese-specific tasks (average)", "0.85")])
add("plamo-2-8b-3bef329a", "plamo2-report", "text", "base model", "score (0–1)", "YES", [("pfgen-bench", "0.753")])
del STATUS["plamo-2-8b-3bef329a"]
del STATUS["gpt-live-1-60f09da9"]
del STATUS["gpt-realtime-21-f3f0c1d7"]
