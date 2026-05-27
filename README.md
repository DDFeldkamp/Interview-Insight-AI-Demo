# Interview Insight Copilot

A lightweight AI engineering demo built for **Great Question**: it turns messy customer-interview transcripts into an evidence-backed research brief with themes, representative quotes, claim-to-evidence maps, risks, next research questions, and automated quality checks.

The point of the demo is not to replace researchers. It is to show how an AI system can accelerate the **raw interviews → trusted product insight** workflow while keeping every generated claim grounded in source evidence.

## Why this demo fits Great Question

Great Question helps teams recruit participants, run customer research, analyze conversations, and share findings. This repo focuses on the AI layer of that workflow: a research repository assistant that ingests interview transcripts, retrieves relevant evidence, synthesizes themes, and produces a reviewable brief.

The demo is intentionally built around trust:

- every finding includes source quotes,
- every claim has an explicit evidence trail,
- evals measure groundedness and coverage,
- researchers can accept, edit, reject, or request more evidence.

## What it does

- Ingests transcript files from `sample_data/interviews/`.
- Parses speaker turns, timestamps, participant metadata, and quoted evidence.
- Builds a local TF-IDF retrieval index by default.
- Supports an optional OpenAI embedding retriever for semantic retrieval.
- Runs retrieval-augmented synthesis over a research objective.
- Supports deterministic local synthesis and optional OpenAI structured synthesis.
- Validates generated output with Pydantic before rendering.
- Repairs/filters LLM citations against a whitelist of extracted evidence candidates.
- Generates claim-to-evidence maps for research auditability.
- Scores the output with eval checks for groundedness, source coverage, claim evidence coverage, redundancy, and multi-source support.
- Exposes both a CLI and a FastAPI web app.
- Captures researcher-in-the-loop feedback as JSONL.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
python tasks.py demo
Get-Content outputs/demo_report.md  # Windows PowerShell
# macOS/Linux: cat outputs/demo_report.md
```

Run tests:

```bash
python tasks.py install-dev
python tasks.py test
```

Run evals:

```bash
python tasks.py eval
Get-Content outputs/eval_results.json  # Windows PowerShell
# macOS/Linux: cat outputs/eval_results.json
```

Run the local web app:

```bash
python tasks.py install-api
python tasks.py serve
```

Then open `http://127.0.0.1:8000` and click **Use sample interviews**.



## Windows / PowerShell note

If `make demo` fails with `make : The term 'make' is not recognized`, use the cross-platform task runner instead:

```powershell
python tasks.py demo
Get-Content outputs/demo_report.md
```

Equivalent commands are available for every Makefile target:

```powershell
python tasks.py install
python tasks.py install-dev
python tasks.py test
python tasks.py eval
python tasks.py install-api
python tasks.py serve
```

You can also run `scripts\demo.bat` or `powershell -ExecutionPolicy Bypass -File scripts\demo.ps1`.

## Dependency versions and install options

The default install is intentionally small and pinned so `pip` does not spend a long time backtracking through broad dependency ranges. Use the smallest install that matches what you want to run:

| Goal | Command | Installs |
|---|---|---|
| Fast CLI demo | `pip install -e .` or `python tasks.py install` | `pydantic`, `python-dotenv` |
| Tests/linting | `python tasks.py install-dev` | default + `pytest`, `ruff` |
| Web UI | `python tasks.py install-api` | default + `fastapi`, `uvicorn`, `python-multipart` |
| OpenAI mode | `python tasks.py install-llm` | default + `openai` |
| Everything | `python tasks.py install-all` | all optional packages |

Pinned package versions are listed in `pyproject.toml` and the `requirements-*.txt` files. The project supports Python `>=3.9,<3.13`; Python 3.11 is still the safest choice for fast wheel installs, but Windows Store Python 3.9 also works.

## Optional LLM mode

The default local mode is deterministic and API-free so reviewers can run the project immediately.

To try OpenAI structured synthesis:

```bash
cp .env.example .env
export OPENAI_API_KEY="your_key_here"
python tasks.py install-llm
python tasks.py openai-demo
```

The OpenAI path still uses retrieval, a quote whitelist, JSON schema validation, evidence repair, and fallback behavior. If the API key is missing or the model returns invalid JSON, the app falls back to the local synthesizer and records `llm_fallback_used` in the eval scores.

To try semantic retrieval with embeddings:

```bash
PYTHONPATH=src python -m gq_insight_copilot.cli synthesize \
  --input sample_data/interviews \
  --objective "Find trust issues in AI-generated interview summaries" \
  --retriever embeddings \
  --out outputs/embedding_report.md \
  --json
```

## Example output

The report includes source-grounded themes and an audit map:

```md
## Theme 1 — AI summaries need visible evidence trails

Finding: Participants trust AI summaries only when the evidence trail is visible.

Evidence:
- "A summary is helpful, but only if I can click into the source." — P01, 00:03:43
- "If I can't click into the source, people treat the summary like vibes." — P04, 00:03:00

Claim-to-evidence map:
Claim: AI summaries become useful for decisions only when each claim can be audited against source quotes.
Why it matters: Stakeholders are more likely to act when they can inspect who said what and in what context.
```

## Architecture

```text
transcripts
  -> parser
  -> chunks
  -> retriever: TF-IDF default, embeddings optional
  -> evidence candidates
  -> local or OpenAI structured synthesizer
  -> Pydantic validation
  -> evidence repair
  -> eval checks
  -> Markdown / HTML report
  -> researcher feedback
```

Key files:

- `src/gq_insight_copilot/ingest.py` — transcript parsing and chunking.
- `src/gq_insight_copilot/vector_store.py` — pure-Python TF-IDF retrieval plus optional OpenAI embeddings.
- `src/gq_insight_copilot/synthesis.py` — local synthesis, OpenAI prompt construction, output validation, and evidence repair.
- `src/gq_insight_copilot/evaluation.py` — groundedness and quality checks.
- `src/gq_insight_copilot/eval_runner.py` — regression-style eval suite.
- `src/gq_insight_copilot/report.py` — Markdown and HTML rendering.
- `src/gq_insight_copilot/api.py` — FastAPI demo and researcher feedback capture.
- `eval/eval_cases.json` — lightweight eval cases.
- `DEMO.md` — short video walkthrough guide.

## What I would build next

- Add diarization/transcription ingestion from video calls.
- Add hybrid BM25 + embedding retrieval with reranking.
- Store researcher feedback as a first-class eval dataset.
- Add segment-aware comparison across roles, company sizes, and research maturity.
- Use active learning to recommend the next best participant segment to recruit.
