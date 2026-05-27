# Architecture

```text
transcripts
  -> parser
  -> overlapping chunks
  -> retriever: TF-IDF by default, OpenAI embeddings optional
  -> evidence candidate whitelist
  -> synthesizer: local deterministic or OpenAI structured JSON
  -> Pydantic schema validation
  -> evidence repair / quote grounding
  -> eval runner
  -> Markdown + HTML report
  -> researcher feedback JSONL
```

## Core ideas

### 1. Grounding first

The pipeline extracts evidence candidates before synthesis. In OpenAI mode, the model is only allowed to use those candidates. After the model returns JSON, the app repairs evidence objects back to the original candidate records and drops citations that do not match the whitelist.

### 2. Structured outputs

The report is represented as a `ResearchBrief` Pydantic model. Themes, evidence, and insight claims are all typed. This makes the app easier to test and makes failures visible before a user sees the result.

### 3. Evals as a product feature

The evaluation module scores:

- `groundedness`: whether quotes appear in the transcript corpus,
- `source_coverage`: how many participants are represented,
- `theme_redundancy`: whether themes are too duplicative,
- `claim_evidence_coverage`: whether claims include supporting quotes,
- `multi_source_theme_rate`: whether themes are supported by more than one participant.

### 4. Human-in-the-loop review

The web app lets a researcher mark a theme as accepted, edited, rejected, or needing more evidence. This creates `outputs/researcher_feedback.jsonl`, which could become training/eval data later.

## Important files

- `ingest.py`: transcript parsing and chunking.
- `vector_store.py`: TF-IDF retriever and optional OpenAI embedding retriever.
- `synthesis.py`: local synthesis, OpenAI prompt construction, structured parsing, and evidence repair.
- `evaluation.py`: automated quality checks.
- `report.py`: Markdown and HTML rendering.
- `eval_runner.py`: regression-style eval cases.
- `api.py`: FastAPI demo and feedback capture.
