"""Eval harness for the KB RAG service.

Runs the full pipeline (via the live HTTP API) over a held-out set of
question/answer/source triples and reports two metrics:

- **recall@5**: did the gold document appear among the top-5 retrieved sources?
  Measures retrieval quality in isolation.
- **faithfulness**: is every claim in the answer supported by the retrieved
  context, as judged by a separate LLM call? Measures generation quality.

Usage:
    python evals/run_evals.py --base-url http://localhost:8000 [--k 5]

Writes evals/results.json and prints a table.
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

import httpx
from openai import AsyncOpenAI

from app.config import settings

HERE = Path(__file__).parent
DATASET = HERE / "dataset.jsonl"
RESULTS = HERE / "results.json"

JUDGE_PROMPT = """\
You are an evaluator. Decide whether every claim in the ANSWER is supported by
the CONTEXT. Ignore style; focus only on factual support. Output JSON with two
fields: "supported_claims" (int) and "total_claims" (int). If there are no
claims, set both to 0.

CONTEXT:
{context}

ANSWER:
{answer}

Reply with JSON only.
"""


def load_dataset() -> list[dict]:
    rows = []
    for line in DATASET.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


async def query_api(client: httpx.AsyncClient, base_url: str, question: str, k: int) -> dict:
    resp = await client.post(f"{base_url}/query", json={"question": question, "top_k": k})
    resp.raise_for_status()
    return resp.json()


async def judge_faithfulness(oai: AsyncOpenAI, answer: str, context: str) -> tuple[int, int]:
    if not answer.strip() or not context.strip():
        return (0, 0)
    prompt = JUDGE_PROMPT.format(context=context[:8000], answer=answer)
    resp = await oai.chat.completions.create(
        model=settings.chat_model,
        temperature=0.0,
        max_tokens=1024,  # reasoning models spend tokens on internal trace before JSON
        messages=[{"role": "user", "content": prompt}],
    )
    # Tolerant JSON parse: provider may wrap JSON in prose or use a reasoning trace.
    text = resp.choices[0].message.content or ""
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    try:
        data = json.loads(m.group(0)) if m else {}
        return int(data.get("supported_claims", 0)), int(data.get("total_claims", 0))
    except (json.JSONDecodeError, ValueError):
        return (0, 0)


async def run(base_url: str, k: int) -> dict:
    rows = load_dataset()
    if not rows:
        print("No eval data found.", file=sys.stderr)
        sys.exit(1)

    oai = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    results = []
    async with httpx.AsyncClient(timeout=120) as client:
        for row in rows:
            q = row["question"]
            gold_doc = row["gold_doc"]
            out = await query_api(client, base_url, q, k)

            retrieved_sources = [h["source"] for h in out.get("retrieved", [])][:k]
            recall = 1 if gold_doc in retrieved_sources else 0

            # Judge context = the FULL text of retrieved passages (what the generator
            # actually saw). Using the 200-char citation snippet here was the original
            # bug — facts often sit beyond the snippet, so the judge falsely scored 0.
            context = "\n\n".join(h.get("content", "") for h in out.get("retrieved", []))

            supported, total = await judge_faithfulness(oai, out.get("answer", ""), context)
            faith = supported / total if total else 0.0

            results.append(
                {
                    "question": q,
                    "gold_doc": gold_doc,
                    "retrieved_sources": retrieved_sources,
                    "recall@k": recall,
                    "answer": out.get("answer", ""),
                    "faithfulness": round(faith, 3),
                    "supported_claims": supported,
                    "total_claims": total,
                }
            )

    mean_recall = sum(r["recall@k"] for r in results) / len(results)
    mean_faith = sum(r["faithfulness"] for r in results) / len(results)
    summary = {
        "n": len(results),
        "k": k,
        "recall@k": round(mean_recall, 3),
        "faithfulness": round(mean_faith, 3),
        "results": results,
    }
    RESULTS.write_text(json.dumps(summary, indent=2))
    return summary


def print_table(summary: dict) -> None:
    print(f"\nEval (n={summary['n']}, k={summary['k']})")
    print("-" * 72)
    print(f"{'recall@' + str(summary['k']):<16} {summary['recall@k']}")
    print(f"{'faithfulness':<16} {summary['faithfulness']}")
    print("-" * 72)
    for r in summary["results"]:
        mark = "ok " if r["recall@k"] else "MISS"
        print(f"[{mark}] faith={r['faithfulness']:.2f}  {r['question'][:48]}")
    print(f"\nWrote {RESULTS}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()
    summary = asyncio.run(run(args.base_url, args.k))
    print_table(summary)


if __name__ == "__main__":
    main()
