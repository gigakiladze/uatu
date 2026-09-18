# Uatu

**Open-source observability, powered by AI.**

Uatu learns a codebase and its project documentation, watches the logs it
produces, and reports real problems — with the specific files and reasoning
behind each diagnosis.

*Named for the Marvel Watcher — observes everything, intervenes in nothing.*

---

## Why

Log platforms are good at storing lines and bad at telling you what matters. A
spike in `500`s becomes a dashboard, not an explanation. Uatu takes the other
approach: it reads your repository and your project description first, builds a
searchable model of what the system is supposed to do, and uses that context to
explain what went wrong.

Cheap statistical filters run first, so the language model only ever sees the
handful of candidates that survive them. That is what keeps cost flat as log
volume grows.

## How it works

Two programs, run at different times. The split is the architecture.

### `learn` — once per project, then on each deploy

```
repository + project description
  → extract knowledge items  (LLM, structured output)
  → embed locally            (sentence-transformers)
  → index into Qdrant        (filtered by project, label)
  → durable copy in MongoDB
```

### `observe` — on a schedule

```
new logs
  → template and reduce       (statistical, no LLM)
  → score against baseline    (new pattern? spike?)
  → retrieve relevant context (vector search)
  → diagnose                  (LLM, cited evidence only)
  → alert
```

## Status

Early, and under active development. What runs today:

- ✅ Project registry and project-scoped knowledge
- ✅ Unstructured document → structured knowledge items, via a LangGraph pipeline
- ✅ Local embeddings and vector search over Qdrant
- ✅ GitHub repository indexing
- ✅ Error diagnosis against indexed knowledge and code
- ✅ Full tracing through LangSmith

On the roadmap:

- ⬜ Input guardrails — prompt-injection and wrong-input detection at ingest
- ⬜ Groundedness verification of generated knowledge
- ⬜ Log ingestion, templating, and statistical baselines
- ⬜ Specialist agents with a lead/verifier pass
- ⬜ Slack alerting with feedback capture

## Stack

| | |
|---|---|
| **MongoDB** | durable storage — projects, knowledge, baselines, feedback |
| **Qdrant** | vector search, filtered by project and knowledge type |
| **LangGraph** | the ingestion and diagnosis pipelines |
| **LangSmith** | tracing and evaluation |
| **Ollama** | local models for extraction and classification |
| **sentence-transformers** | embeddings, run locally — no API calls |
| **FastAPI** | HTTP interface |

Python 3.12, dependencies managed with [uv](https://github.com/astral-sh/uv).

## Quick start

```bash
git clone https://github.com/<you>/uatu.git
cd uatu

cp .env.example .env      # then fill it in
docker compose up -d      # MongoDB + Qdrant
uv sync

uv run uvicorn uatu.api.app:app --reload
```

Uatu uses local models by default, so you also need [Ollama](https://ollama.com):

```bash
ollama pull qwen2.5-coder:14b
```

Then open http://localhost:8000/docs.

### Teach it a project

```bash
# 1. register the project
curl -X POST localhost:8000/projects/ \
  -H 'content-type: application/json' \
  -d '{"name": "my-app", "description": "checkout service"}'

# 2. feed it a description — it extracts the structured facts itself
python -c "
from uatu.graphs.ingest.graph import graph
graph.invoke({'project_id': '<id from step 1>', 'raw_text': open('DESIGN.md').read()})
"

# 3. ask it something
curl -X POST localhost:8000/projects/<id>/knowledge/search \
  -H 'content-type: application/json' \
  -d '{"query": "how are refunds handled?"}'
```

## Design notes

**The model never sees raw logs.** Only candidates that survive statistical
filtering reach it. This is the difference between a system that scales and a
demo that does not.

**Project knowledge lives in the index, not the code.** Adding a second project
means running `learn` again — never editing source. Language support, log
sources, and notification channels are adapter boundaries.

**Extraction copies, it does not paraphrase.** Stored knowledge is the author's
own words, so every retrieved fact can be traced back to something a human
wrote.

## Configuration

See `.env.example`. Everything is environment-driven — no per-project config
files, by design.

## Contributing

Issues and pull requests are welcome. If you are proposing a design change,
open an issue first so the tradeoff can be discussed before code is written.

## License

MIT — see [LICENSE](LICENSE).
