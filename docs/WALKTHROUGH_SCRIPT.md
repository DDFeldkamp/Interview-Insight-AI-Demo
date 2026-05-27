# 2-3 Minute Walkthrough Script

## 0:00 — Context

"I built Interview Insight Copilot as a lightweight AI engineering demo for Great Question. The goal is to show how AI can help turn customer interviews into trusted product insights without losing the source evidence."

## 0:20 — Run the pipeline

```bash
make demo
cat outputs/demo_report.md
```

"The input is a small set of markdown interview transcripts. The system parses participant metadata, chunks the transcript, retrieves relevant evidence, and generates a research brief."

## 0:45 — Show the output

"The important part is that this is not just a generic summary. Each theme has participant quotes, a product opportunity, a risk, and a next research question. I also added a claim-to-evidence map so the researcher can audit why the AI made each claim."

## 1:20 — Show evals

```bash
make eval
cat outputs/eval_results.json
```

"I added lightweight evals because research synthesis needs trust. The eval suite checks whether quotes are grounded in the source transcript, whether the report covers enough participants, whether claims include evidence, and whether themes are redundant."

## 1:50 — Show the web demo

```bash
make serve
```

"The FastAPI demo has a sample-study button, an upload flow, eval badges, expandable evidence, and a researcher review form. Feedback is saved to JSONL, which could later become a regression eval or fine-tuning signal."

## 2:20 — Explain optional LLM mode

"The default is deterministic so anyone can run it without an API key. But I also added an OpenAI structured-output path. The model receives a whitelist of evidence candidates, returns JSON, and the app validates the schema and repairs citations back to the original evidence objects before rendering. If anything fails, it falls back safely."

## 2:50 — Close

"The project is intentionally small, but it shows the AI engineering ideas I would bring to Great Question: retrieval, grounding, structured outputs, evals, human review, and product thinking around customer research workflows."
