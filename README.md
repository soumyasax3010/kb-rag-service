---
title: KB RAG Service
emoji: 📚
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# KB RAG Service

A knowledge-base service backed by **retrieval-augmented generation**. Upload
documents, ask questions, get answers **cited back to source passages**. Built
with FastAPI, Postgres + pgvector, and any **OpenAI-compatible** embedding/chat
endpoint (defaults to Fireworks; OpenAI is a one-line switch) — and shipped with
an **eval harness** that reports recall@5 and faithfulness so changes are
measurable.

> Resume-anchor project. The point is engineering judgment, not a demo: a real
> vector store, citations as a first-class output, a provider-agnostic client,
> and numbers in the README.

<!-- badges -->
![CI](https://github.com/soumyasax3010/kb-rag-service/actions/workflows/ci.yml/badge.svg)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)

## Live demo

<!-- TODO: pin deployed URL + demo GIF here. CI must be green before claiming it. -->

## How it works

```mermaid
flowchart LR
    U[Client] --> API[FastAPI]
    subgraph Ingest
        L[Loader PDF/MD/TXT] --> C[Chunker tokens+overlap] --> E[Embed] --> PG[(Postgres+pgvector)]
    end
    subgraph Query
        Q[Embed question] --> S[Vector cosine search top-k] --> G[LLM cited answer]
    end
    API --> Ingest
    API --> Query
    S --> PG
    G --> U
```

- **Ingest** (`POST /documents`): parse → token-based chunking (512 tok, 64
  overlap) → embed (`nomic-ai/nomic-embed-text-v1.5`, 768-dim by default) →
  store in pgvector with `(document_id, chunk_idx, source, content)`.
- **Query** (`POST /query`): embed the question → cosine search top-k over an
  HNSW index → feed numbered passages to the chat model (`glm-5p2` by default)
  instructed to cite by passage number → map `[n]` markers back to concrete
  chunks → return `{answer, retrieved[], citations[]}`.

## Quickstart

Requirements: `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and
Postgres with the pgvector extension.

**Postgres + pgvector** — pick one:

```bash
# Option A: Docker (uses the pgvector/pgvector:pg16 image in docker-compose.yml)
docker compose up -d

# Option B: macOS via Homebrew (pgvector bottle targets postgresql@17)
brew install postgresql@17 pgvector
brew services start postgresql@17
psql -d postgres -c "CREATE ROLE kb WITH LOGIN PASSWORD 'kb';"
psql -d postgres -c "CREATE DATABASE kb OWNER kb;"
psql -d kb -c "CREATE EXTENSION vector;"
```

**Run the service:**

```bash
cp .env.example .env       # set OPENAI_API_KEY (+ OPENAI_BASE_URL if not OpenAI)
uv sync --extra dev
uv run alembic upgrade head

uv run uvicorn app.main:app --reload
curl localhost:8000/health
# ingest the bundled sample corpus
for f in sample_corpus/*.md; do curl -s -F "file=@$f" localhost:8000/documents; done
# ask
curl -s -XPOST localhost:8000/query -H 'Content-Type: application/json' \
  -d '{"question":"What are the three stages of RAG?"}' | jq
```

The default `.env.example` is configured for **Fireworks** (OpenAI-compatible).
For OpenAI: unset `OPENAI_BASE_URL`, set `EMBED_MODEL=text-embedding-3-small`,
`EMBED_DIM=1536`, `CHAT_MODEL=gpt-4o-mini`, then re-run `alembic downgrade base
&& alembic upgrade head` (the vector column dim is read from `EMBED_DIM`).

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/documents` | multipart `file` | `{document: {id, source, title, num_chunks}}` |
| `GET` | `/documents` | — | `[{id, source, title, num_chunks}, ...]` |
| `DELETE` | `/documents/{id}` | — | 204 |
| `POST` | `/query` | `{question, top_k?}` | `{question, answer, retrieved[], citations[]}` |
| `GET` | `/health` | — | `{status: "ok"}` |

`citations[]` = the chunks the model chose to cite (with source + snippet);
`retrieved[]` = the full top-k actually retrieved (with cosine distance) — useful
for debugging retrieval and for the eval harness.

## Deploy (live demo, no credit card)

Two free accounts: **Supabase** for Postgres+pgvector, **Hugging Face Space**
(Docker SDK) for the app. No card needed on either.

### 1. Supabase — database

1. Create a free project at supabase.com.
2. Dashboard → **Database → Extensions** → enable `vector`.
3. Dashboard → **Project Settings → Database → Connection string → URI** → copy
   the **direct** string (host `db.<ref>.supabase.co:5432`), e.g.
   `postgresql://postgres:[PW]@db.<ref>.supabase.co:5432/postgres`.
4. Convert to the asyncpg form (note the `+asyncpg`):
   `postgresql+asyncpg://postgres:[PW]@db.<ref>.supabase.co:5432/postgres`

### 2. Hugging Face Space — app

1. Create a Space at huggingface.co → SDK **Docker** → blank.
2. Space **Settings → Variables and secrets**, add:

   | Name | Value |
   |---|---|
   | `OPENAI_API_KEY` (secret) | your Fireworks key |
   | `OPENAI_BASE_URL` | `https://api.fireworks.ai/inference/v1` |
   | `DATABASE_URL` (secret) | the Supabase asyncpg URL from step 1.4 |
   | `DATABASE_SSL` | `true` |
   | `EMBED_MODEL` | `nomic-ai/nomic-embed-text-v1.5` |
   | `EMBED_DIM` | `768` |
   | `CHAT_MODEL` | `accounts/fireworks/models/glm-5p2` |

3. Push the code to the Space's git (HF hosts its own git — this is not GitHub):

   ```bash
   cd kb-rag-service
   git remote add space https://huggingface.co/spaces/<your-user>/<space-name>
   git push space main
   ```

4. HF builds the image, runs `alembic upgrade head` (creates tables + HNSW index
   in Supabase), then serves uvicorn on 7860. On first start the app **auto-seeds**
   the bundled sample corpus into Supabase (only if empty), so the demo just works.

5. Demo URL: `https://<your-user>-<space-name>.hf.space`. Test:

   ```bash
   curl https://<your-user>-<space-name>.hf.space/health
   curl -XPOST https://<your-user>-<space-name>.hf.space/query \
     -H 'Content-Type: application/json' \
     -d '{"question":"What are the three stages of RAG?"}'
   ```

Notes: HF free CPU Spaces sleep when idle — the first request after sleep takes
~30s to wake. If startup fails, check the Space **Logs** tab (most often a wrong
`DATABASE_URL` or missing `vector` extension). For OpenAI instead of Fireworks,
set the env vars accordingly and `EMBED_DIM=1536`.

## Evaluation

```bash
uv run python evals/run_evals.py --k 5
```

Reports **recall@5** (retrieval) and **faithfulness** (LLM-judged generation)
over 15 hand-labeled Q&A pairs in `evals/dataset.jsonl`, and writes
`evals/results.json`.

| Metric | Score | Notes |
|---|---|---|
| recall@5 | **1.00** | every gold doc retrieved in top-5 |
| faithfulness | **0.93** | 14/15 answers fully grounded; 1 was a judge false-negative (answer was correct + cited, judge returned 0/0) |

Provider for this run: Fireworks — embeddings `nomic-ai/nomic-embed-text-v1.5`
(768-dim), chat `accounts/fireworks/models/glm-5p2`. See `evals/README.md`.

## Design decisions

- **pgvector over a dedicated vector DB** — one service to run, keeps document
  metadata and embeddings in the same transactional store, and shows SQL+vector
  skills. Cosine distance via the `<=>` operator on an HNSW index (`vector_cosine_ops`).
  HNSW over ivfflat: better recall at similar latency, no training step. Tradeoff:
  HNSW uses more memory; for very large corpora ivfflat can win once tuned.
- **Token-based chunking with overlap (512/64)** — defensible default for prose;
  overlap prevents context loss at boundaries. The chunker is a pure function in
  its own module, so it's unit-tested without a DB and swappable for
  sentence/semantic chunking.
- **OpenAI behind a thin, provider-agnostic client** — all embedding/chat calls
  go through `app/retrieval/embed.py` and `app/generation/answer.py` plus
  `app/config.py`. The OpenAI SDK talks to any OpenAI-compatible endpoint, so
  switching between OpenAI, Fireworks, or a local server is a `.env` change
  (`OPENAI_BASE_URL` + model ids + `EMBED_DIM`). This repo runs on Fireworks by
  default; OpenAI needs only the swap described in Quickstart.
- **Citations are first-class** — chunks keep `(document_id, chunk_idx, source)`;
  the prompt forces `[n]` citation and the router resolves markers to concrete
  chunks with snippets. This is what separates a KB tool from "ChatGPT + a PDF."
- **Evals as a core feature** — a held-out labeled set and two independent
  metrics (retrieval vs. generation) tracked as numbers, not vibes.

## Project layout

```
app/            config, db, models, schemas, main
  ingest/       loader, chunker, pipeline
  retrieval/    embed, search
  generation/   answer
  routers/      documents, query
alembic/        migrations (CREATE EXTENSION vector + HNSW index)
evals/          dataset.jsonl, run_evals.py, README
sample_corpus/  5 markdown docs so the demo + evals work out of the box
tests/          chunker (unit), api (smoke), search (integration)
```

## License

MIT
