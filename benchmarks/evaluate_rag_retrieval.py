"""Evaluate RAG retrieval against paraphrased questions without calling an LLM.

Run from the repository root:
    .\\.venv\\Scripts\\python.exe benchmarks\\evaluate_rag_retrieval.py

Requires the local Qdrant collection to be indexed. If it is missing or stale,
run:
    .\\.venv\\Scripts\\python.exe -m src.rag.ingest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATASET_PATH = ROOT / "benchmarks" / "datasets" / "rag_retrieval_paraphrases.json"


def main() -> int:
    from src.rag.retriever import retrieve_knowledge

    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    top_k = int(dataset.get("retrieval_top_k", 5))
    total = 0
    hits = 0
    reciprocal_ranks: list[float] = []

    print("ORKA.AI — OFFLINE RAG RETRIEVAL EVALUATION")
    print(f"Supporting-document cutoff: top {top_k}")
    print("LLM calls: 0 | Langfuse calls: 0")
    print("=" * 72)

    for group in dataset["groups"]:
        group_total = 0
        group_hits = 0
        print(f"\n[{group['id']}] Expected SQL example:")
        print(f"  {group['target_source']}")

        for question in group["variants"]:
            results = retrieve_knowledge(
                question,
                top_k=top_k,
                schema_top_k=8,
            )
            supporting = [
                item for item in results
                if item["type"] != "schema"
            ][:top_k]

            matching_rank = next(
                (
                    rank
                    for rank, item in enumerate(supporting, start=1)
                    if item["type"] == "sql_example"
                    and item["source"].casefold() == group["target_source"].casefold()
                ),
                None,
            )

            total += 1
            group_total += 1
            if matching_rank is not None:
                hits += 1
                group_hits += 1
                reciprocal_ranks.append(1.0 / matching_rank)
                status = f"HIT@{top_k} (rank {matching_rank})"
            else:
                reciprocal_ranks.append(0.0)
                status = f"MISS@{top_k}"

            print(f"\n  {status}: {question}")
            print("  Retrieved supporting documents:")
            for rank, item in enumerate(supporting, start=1):
                print(
                    f"    {rank}. {item['type']} | {item['source']} "
                    f"| RRF={item['score']:.6f}"
                )

        group_rate = group_hits / group_total if group_total else 0.0
        print(
            f"\n  Group result: {group_hits}/{group_total} "
            f"({group_rate:.1%})"
        )

    hit_rate = hits / total if total else 0.0
    mrr = sum(reciprocal_ranks) / total if total else 0.0
    print("\n" + "=" * 72)
    print(f"TOTAL: {hits}/{total} relevant examples retrieved in top {top_k}")
    print(f"Hit@{top_k}: {hit_rate:.1%}")
    print(f"MRR: {mrr:.4f}")
    print("\nInterpretation:")
    print("- Hit@K measures whether the expected SQL example appears in the top K supporting documents.")
    print("- MRR rewards retrieving the expected example closer to rank 1.")
    print("- These metrics evaluate retrieval only, not SQL generation or execution.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"RAG retrieval evaluation could not complete: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print(
            "Check that the local Qdrant collection exists and was reindexed "
            "after the latest SQL-example changes.",
            file=sys.stderr,
        )
        raise SystemExit(1)
