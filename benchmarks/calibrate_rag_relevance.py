"""Calibrate an experimental RAG relevance threshold using labeled robustness queries.

This is diagnostic only: it does not change production retrieval behavior.
Run from the repository root:
    .\\.venv\\Scripts\\python.exe benchmarks\\calibrate_rag_relevance.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# When run as a script, Python puts benchmarks/ on sys.path, not the repo root.
sys.path.insert(0, str(ROOT))
DATASET_PATH = ROOT / "benchmarks" / "datasets" / "rag_retrieval_robustness.json"


def confusion_at_threshold(rows: list[dict], threshold: float) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted_relevant = row["max_semantic_score"] >= threshold
        if row["is_in_domain"] and predicted_relevant:
            tp += 1
        elif not row["is_in_domain"] and predicted_relevant:
            fp += 1
        elif not row["is_in_domain"] and not predicted_relevant:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def main() -> int:
    from src.rag.retriever import retrieve_knowledge

    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    rows: list[dict] = []
    all_docs = 1000

    print("ORKA.AI — OFFLINE RELEVANCE THRESHOLD CALIBRATION")
    print("Diagnostic only; production retrieval is unchanged.")
    print("Groq calls: 0 | Langfuse calls: 0")
    print("=" * 78)

    for case in dataset["cases"]:
        # Request all schema and supporting documents so the maximum semantic
        # similarity is not limited by the normal top-k cutoffs.
        results = retrieve_knowledge(
            case["question"],
            top_k=all_docs,
            schema_top_k=all_docs,
        )
        max_score = max(
            (float(item.get("semantic_score", 0.0)) for item in results),
            default=0.0,
        )
        row = {
            "id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "is_in_domain": bool(case.get("expected_document_ids")),
            "max_semantic_score": max_score,
        }
        rows.append(row)
        label = "IN-DOMAIN" if row["is_in_domain"] else "OUT-OF-DOMAIN"
        print(f'{row["id"]:<30} {label:<13} max_semantic={max_score:.6f}')

    positives = [r["max_semantic_score"] for r in rows if r["is_in_domain"]]
    negatives = [r["max_semantic_score"] for r in rows if not r["is_in_domain"]]
    print("\nScore ranges:")
    print(f"  In-domain:     min={min(positives):.6f}, max={max(positives):.6f}")
    print(f"  Out-of-domain: min={min(negatives):.6f}, max={max(negatives):.6f}")

    # Evaluate midpoints between adjacent observed scores. These are candidate
    # cutoffs for this labeled sample, not universal confidence thresholds.
    scores = sorted({r["max_semantic_score"] for r in rows})
    candidates = sorted({0.0, 1.0, *(
        (left + right) / 2.0 for left, right in zip(scores, scores[1:])
    )})

    ranked = []
    for threshold in candidates:
        cm = confusion_at_threshold(rows, threshold)
        total = len(rows)
        accuracy = (cm["tp"] + cm["tn"]) / total if total else 0.0
        recall = cm["tp"] / (cm["tp"] + cm["fn"]) if cm["tp"] + cm["fn"] else 0.0
        specificity = cm["tn"] / (cm["tn"] + cm["fp"]) if cm["tn"] + cm["fp"] else 0.0
        precision = cm["tp"] / (cm["tp"] + cm["fp"]) if cm["tp"] + cm["fp"] else 0.0
        ranked.append((accuracy, recall, specificity, precision, threshold, cm))

    ranked.sort(key=lambda item: (item[0], item[2], item[1]), reverse=True)
    print("\nBest candidate cutoffs on this small labeled set:")
    print("threshold  accuracy  precision  recall  specificity  TP FP TN FN")
    for accuracy, recall, specificity, precision, threshold, cm in ranked[:8]:
        print(
            f"{threshold:9.6f}  {accuracy:8.1%}  {precision:9.1%}  "
            f"{recall:6.1%}  {specificity:11.1%}  "
            f'{cm["tp"]:2d} {cm["fp"]:2d} {cm["tn"]:2d} {cm["fn"]:2d}'
        )

    print("\nLimitations:")
    print("- Only 11 manually labeled questions are evaluated (8 positive, 3 negative).")
    print("- A query is labeled in-domain when expected_document_ids is non-empty.")
    print("- Maximum semantic similarity is a heuristic, not a calibrated probability.")
    print("- Use these results to decide whether more labeled examples are needed;")
    print("  do not deploy a threshold based only on this small sample.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"Relevance calibration failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
