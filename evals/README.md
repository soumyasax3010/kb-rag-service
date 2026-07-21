# Evaluation harness

Measures two things independently, so a change to chunking or retrieval can be
tracked:

- **recall@k** — did the gold document appear among the top-k retrieved sources?
  Measures retrieval in isolation.
- **faithfulness** — is every claim in the answer supported by the retrieved
  context, judged by a separate LLM call? Measures generation quality.

## Run

The service must be running and the sample corpus ingested:

```bash
uv run uvicorn app.main:app --reload
# in another shell, ingest the sample corpus:
for f in sample_corpus/*.md; do
  curl -s -F "file=@$f" http://localhost:8000/documents
done
# then:
uv run python evals/run_evals.py --base-url http://localhost:8000 --k 5
```

Writes `results.json` and prints a per-question table plus the two headline
scores. Put those two numbers in the top-level README's eval table.

## Dataset

`dataset.jsonl` holds 15 hand-written `{question, gold_answer, gold_doc}` rows
over `sample_corpus/`. Swap in your own corpus + dataset to evaluate your own
knowledge base; keep the same JSONL shape.
