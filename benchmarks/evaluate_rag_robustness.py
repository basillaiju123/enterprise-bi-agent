"""Expanded offline RAG retrieval robustness evaluation.

No Groq or Langfuse calls are made. The script evaluates retrieval against
manually labeled document IDs from the current sample warehouse knowledge base.

Run from the repository root:
    .\\.venv\\Scripts\\python.exe benchmarks\\evaluate_rag_robustness.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATASET_PATH = ROOT / "benchmarks" / "datasets" / "rag_retrieval_robustness.json"


def main() -> int:
    from src.rag.retriever import retrieve_knowledge

    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    support_k = int(dataset.get("supporting_top_k", 5))
    schema_k = int(dataset.get("schema_top_k", 8))

    expected_total = 0
    expected_retrieved = 0
    first_relevant_rr: list[float] = []
    negative_total = 0
    negative_clean = 0
    category_stats = defaultdict(lambda: {"queries": 0, "expected": 0, "retrieved": 0})

    print("ORKA.AI — EXPANDED OFFLINE RAG ROBUSTNESS EVALUATION")
    print(f"Supporting top-k: {support_k} | Schema top-k: {schema_k}")
    print("Groq calls: 0 | Langfuse calls: 0")
    print("=" * 78)

    for case in dataset["cases"]:
        results = retrieve_knowledge(
            case["question"],
            top_k=support_k,
            schema_top_k=schema_k,
        )
        schema_results = [item for item in results if item["type"] == "schema"][:schema_k]
        supporting_results = [item for item in results if item["type"] != "schema"][:support_k]
        ranked = schema_results + supporting_results
        ranks = {
            item["document_id"]: rank
            for rank, item in enumerate(ranked, start=1)
        }

        expected_ids = case.get("expected_document_ids", [])
        forbidden_ids = set(case.get("forbidden_document_ids", []))
        retrieved_expected = [doc_id for doc_id in expected_ids if doc_id in ranks]
        missing_expected = [doc_id for doc_id in expected_ids if doc_id not in ranks]
        category = case["category"]
        stats = category_stats[category]
        stats["queries"] += 1
        stats["expected"] += len(expected_ids)
        stats["retrieved"] += len(retrieved_expected)
        expected_total += len(expected_ids)
        expected_retrieved += len(retrieved_expected)

        if expected_ids:
            best_rank = min((ranks[doc_id] for doc_id in retrieved_expected), default=None)
            first_relevant_rr.append(1.0 / best_rank if best_rank else 0.0)
            query_status = "HIT" if not missing_expected else "PARTIAL" if retrieved_expected else "MISS"
        else:
            first_relevant_rr.append(0.0)
            query_status = "NEGATIVE"

        forbidden_found = [
            item["document_id"]
            for item in ranked
            if item["document_id"] in forbidden_ids
        ]
        if category == "out_of_domain_negative":
            negative_total += 1
            if not forbidden_found:
                negative_clean += 1

        print(f"\\n[{case['id']}] {query_status} — {case['question']}")
        if expected_ids:
            print(f"  Expected docs retrieved: {len(retrieved_expected)}/{len(expected_ids)}")
            if missing_expected:
                print(f"  Missing expected IDs: {', '.join(missing_expected)}")
            if retrieved_expected:
                print("  Retrieved expected ranks: " + ", ".join(
                    f"{doc_id} (rank {ranks[doc_id]})" for doc_id in retrieved_expected
                ))
        if forbidden_ids:
            print(
                "  Forbidden target examples in retrieved set: "
                + (", ".join(forbidden_found) if forbidden_found else "none")
            )

        print("  Schema results:")
        for rank, item in enumerate(schema_results, start=1):
            print(f"    S{rank}. {item['document_id']} | RRF={item['score']:.6f}")
        print("  Supporting results:")
        for rank, item in enumerate(supporting_results, start=1):
            print(f"    K{rank}. {item['document_id']} | RRF={item['score']:.6f}")

    recall = expected_retrieved / expected_total if expected_total else 0.0
    mrr = sum(first_relevant_rr) / len(first_relevant_rr) if first_relevant_rr else 0.0
    negative_clean_rate = negative_clean / negative_total if negative_total else 0.0

    print("\\n" + "=" * 78)
    print(f"Expected-document recall: {expected_retrieved}/{expected_total} ({recall:.1%})")
    print(f"MRR (first relevant document, per query): {mrr:.4f}")
    print(f"Negative-query cleanliness: {negative_clean}/{negative_total} ({negative_clean_rate:.1%})")
    print("\\nBy category:")
    for category, stats in sorted(category_stats.items()):
        if stats["expected"]:
            score = stats["retrieved"] / stats["expected"]
            detail = f"{stats['retrieved']}/{stats['expected']} expected docs ({score:.1%})"
        else:
            detail = "negative-query contamination checked separately"
        print(f"  {category}: {stats['queries']} queries; {detail}")

    print("\\nInterpretation:")
    print("- Expected-document recall measures labeled knowledge coverage in the retrieved set.")
    print("- MRR uses the rank of the first expected document; schema and supporting channels are shown separately.")
    print("- Negative-query cleanliness checks only whether the three targeted SQL examples appear.")
    print("- These are manually labeled retrieval checks, not an LLM-generation or full out-of-domain rejection test.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"RAG robustness evaluation failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print(
            "Ensure the local Qdrant collection is indexed and the retriever "
            "returns document_id metadata.",
            file=sys.stderr,
        )
        raise SystemExit(1)
