from __future__ import annotations

import html
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from .report import render_html, render_markdown
from .synthesis import synthesize_from_directory

app = FastAPI(title="Interview Insight Copilot")
REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = REPO_ROOT / "sample_data" / "interviews"


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!doctype html>
    <html>
      <head>
        <title>Interview Insight Copilot</title>
        <style>
          body { font-family: Inter, ui-sans-serif, system-ui, sans-serif; max-width: 1040px; margin: 48px auto; line-height: 1.5; background: #f7f7fb; color: #16161d; padding: 0 20px; }
          textarea { width: 100%; min-height: 92px; border-radius: 14px; border: 1px solid #d9d9e8; padding: 12px; font: inherit; }
          input, button, select { font-size: 1rem; margin-top: 8px; }
          button { border: 0; border-radius: 12px; background: #20243a; color: white; padding: 10px 14px; cursor: pointer; }
          .card { background: white; border: 1px solid #e7e7ef; border-radius: 24px; padding: 28px; box-shadow: 0 12px 32px rgba(25, 25, 40, .06); margin-bottom: 18px; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
          .muted { color: #69697a; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Interview Insight Copilot</h1>
          <p class="muted">A Great Question-style AI demo: retrieve transcript evidence, synthesize grounded themes, expose eval scores, and let a researcher review the output.</p>
        </div>

        <div class="grid">
          <div class="card">
            <h2>Run sample study</h2>
            <form action="/sample" method="post">
              <label>Research objective</label><br />
              <textarea name="objective">Find onboarding and research-repository friction for product managers</textarea><br />
              <label>Provider</label><br />
              <select name="provider">
                <option value="local">local deterministic</option>
                <option value="openai">OpenAI with validated fallback</option>
              </select><br />
              <button type="submit">Use sample interviews</button>
            </form>
          </div>

          <div class="card">
            <h2>Upload transcripts</h2>
            <form action="/synthesize" enctype="multipart/form-data" method="post">
              <label>Research objective</label><br />
              <textarea name="objective">What should we improve in the research workflow?</textarea><br />
              <label>Transcript files</label><br />
              <input name="files" type="file" multiple accept=".md" /><br />
              <label>Provider</label><br />
              <select name="provider">
                <option value="local">local deterministic</option>
                <option value="openai">OpenAI with validated fallback</option>
              </select><br />
              <button type="submit">Generate brief</button>
            </form>
          </div>
        </div>
      </body>
    </html>
    """


@app.post("/sample", response_class=HTMLResponse)
async def synthesize_sample(objective: str = Form(...), provider: str = Form("local")) -> str:
    brief = synthesize_from_directory(SAMPLE_DIR, objective=objective, provider=provider)
    return render_html(brief)


@app.post("/synthesize", response_class=HTMLResponse)
async def synthesize(
    objective: str = Form(...),
    provider: str = Form("local"),
    files: list[UploadFile] = File(...),
) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for file in files:
            content = await file.read()
            safe_name = Path(file.filename or "transcript.md").name
            (tmp_path / safe_name).write_bytes(content)
        brief = synthesize_from_directory(tmp_path, objective=objective, provider=provider)
        return render_html(brief)


@app.post("/feedback", response_class=HTMLResponse)
async def save_feedback(
    theme_title: str = Form(...), status: str = Form(...), note: str = Form("")
) -> str:
    output_dir = REPO_ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    record = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "theme_title": theme_title,
        "status": status,
        "note": note,
    }
    feedback_path = output_dir / "researcher_feedback.jsonl"
    with feedback_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    safe_theme = html.escape(theme_title)
    safe_status = html.escape(status)
    return f"""
    <html><body style="font-family: system-ui; max-width: 720px; margin: 48px auto;">
      <h1>Feedback saved</h1>
      <p>Saved researcher review for <strong>{safe_theme}</strong> as <strong>{safe_status}</strong>.</p>
      <p>This creates a simple human-in-the-loop feedback artifact at <code>outputs/researcher_feedback.jsonl</code>.</p>
      <p><a href="/">Back to demo</a></p>
    </body></html>
    """


@app.post("/synthesize-markdown")
async def synthesize_markdown(objective: str = Form(...), files: list[UploadFile] = File(...)) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for file in files:
            safe_name = Path(file.filename or "transcript.md").name
            (tmp_path / safe_name).write_bytes(await file.read())
        brief = synthesize_from_directory(tmp_path, objective=objective)
        return render_markdown(brief)
