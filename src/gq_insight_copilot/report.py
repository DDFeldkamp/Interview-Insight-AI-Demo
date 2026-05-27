from __future__ import annotations

import html

from .models import Evidence, InsightClaim, ResearchBrief, Theme


def render_markdown(brief: ResearchBrief) -> str:
    lines: list[str] = []
    lines.append("# AI Research Brief")
    lines.append("")
    lines.append(f"**Objective:** {brief.objective}")
    lines.append("")
    lines.append("## Executive summary")
    lines.append(brief.executive_summary)
    lines.append("")
    lines.append("## Themes")
    lines.append("")
    for index, theme in enumerate(brief.themes, start=1):
        lines.extend(_render_theme(index, theme))
        lines.append("")
    lines.append("## Claim-to-evidence map")
    lines.append("")
    lines.append("| Theme | Claim | Why it matters | Evidence |")
    lines.append("|---|---|---|---|")
    for theme in brief.themes:
        for claim in theme.claims:
            evidence = "<br>".join(_format_evidence(e) for e in claim.evidence)
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_table(theme.title),
                        _escape_table(claim.claim),
                        _escape_table(claim.why_it_matters),
                        _escape_table(evidence),
                    ]
                )
                + " |"
            )
    lines.append("")
    lines.append("## Surprising quotes")
    lines.append("")
    for evidence in brief.surprising_quotes:
        lines.append(f"- {_format_evidence(evidence)}")
    lines.append("")
    lines.append("## Recommended next steps")
    lines.append("")
    for step in brief.recommended_next_steps:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("## Automated eval checks")
    lines.append("")
    for metric, value in brief.eval_scores.items():
        lines.append(f"- **{metric}:** {value}")
    lines.append("")
    return "\n".join(lines)


def render_html(brief: ResearchBrief) -> str:
    theme_cards = "\n".join(_render_theme_html(i, theme) for i, theme in enumerate(brief.themes, 1))
    eval_badges = "\n".join(
        f'<span class="badge"><strong>{html.escape(metric)}</strong> {value}</span>'
        for metric, value in brief.eval_scores.items()
    )
    next_steps = "\n".join(f"<li>{html.escape(step)}</li>" for step in brief.recommended_next_steps)
    quotes = "\n".join(f"<li>{_format_evidence_html(e)}</li>" for e in brief.surprising_quotes)
    return f"""
    <!doctype html>
    <html>
      <head>
        <title>Interview Insight Copilot Report</title>
        <style>
          :root {{ color-scheme: light; }}
          body {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #f7f7fb; color: #16161d; margin: 0; }}
          main {{ max-width: 1120px; margin: 0 auto; padding: 40px 24px 72px; }}
          .hero {{ background: linear-gradient(135deg, #20243a, #4b4f7a); color: white; border-radius: 28px; padding: 32px; box-shadow: 0 20px 60px rgba(28, 31, 55, .18); }}
          .hero p {{ max-width: 820px; color: #e9e9ff; }}
          .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin-top: 22px; }}
          .card {{ background: white; border: 1px solid #e7e7ef; border-radius: 22px; padding: 22px; box-shadow: 0 12px 32px rgba(25, 25, 40, .06); }}
          .badge {{ display: inline-block; background: #eef0ff; border: 1px solid #dfe2ff; border-radius: 999px; padding: 8px 11px; margin: 4px; font-size: .88rem; }}
          .quote {{ border-left: 4px solid #6b6eea; padding-left: 12px; color: #36364a; }}
          details {{ margin-top: 14px; }}
          summary {{ cursor: pointer; font-weight: 700; }}
          .claim {{ background: #fbfbff; border: 1px solid #ededf7; border-radius: 16px; padding: 14px; margin: 12px 0; }}
          label {{ font-weight: 650; }}
          select, input, button {{ font: inherit; }}
          button {{ border: 0; border-radius: 12px; background: #20243a; color: white; padding: 9px 13px; cursor: pointer; }}
          .muted {{ color: #68687a; }}
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <h1>AI Research Brief</h1>
            <p><strong>Objective:</strong> {html.escape(brief.objective)}</p>
            <p>{html.escape(brief.executive_summary)}</p>
          </section>

          <section class="card" style="margin-top: 22px;">
            <h2>Automated eval checks</h2>
            <p class="muted">These lightweight checks make the demo less of a black-box summarizer: quotes must be grounded, source coverage is tracked, and claims are expected to carry evidence.</p>
            {eval_badges}
          </section>

          <section class="grid">
            {theme_cards}
          </section>

          <section class="card" style="margin-top: 22px;">
            <h2>Surprising quotes</h2>
            <ul>{quotes}</ul>
          </section>

          <section class="card" style="margin-top: 22px;">
            <h2>Recommended next steps</h2>
            <ol>{next_steps}</ol>
          </section>
        </main>
      </body>
    </html>
    """


def _render_theme(index: int, theme: Theme) -> list[str]:
    lines = [
        f"### Theme {index} — {theme.title}",
        f"**Confidence:** {theme.confidence}",
        f"**Participants:** {', '.join(theme.participants)}",
        "",
        f"**Finding:** {theme.finding}",
        "",
        "**Evidence:**",
    ]
    for evidence in theme.evidence:
        lines.append(f"- {_format_evidence(evidence)}")
    lines.append("")
    lines.append("**Claims:**")
    for claim in theme.claims:
        lines.extend(_render_claim(claim))
    lines.extend(
        [
            "",
            f"**Product opportunity:** {theme.product_opportunity}",
            f"**Risk if ignored:** {theme.risk_if_ignored}",
            f"**Next research question:** {theme.next_question}",
        ]
    )
    return lines


def _render_claim(claim: InsightClaim) -> list[str]:
    lines = [
        f"- **Claim:** {claim.claim}",
        f"  - **Why it matters:** {claim.why_it_matters}",
    ]
    for evidence in claim.evidence:
        lines.append(f"  - **Evidence:** {_format_evidence(evidence)}")
    return lines


def _render_theme_html(index: int, theme: Theme) -> str:
    evidence_items = "\n".join(f"<li>{_format_evidence_html(e)}</li>" for e in theme.evidence)
    claim_blocks = "\n".join(_render_claim_html(claim) for claim in theme.claims)
    feedback_form = f"""
      <form method="post" action="/feedback">
        <input type="hidden" name="theme_title" value="{html.escape(theme.title)}" />
        <label>Researcher review</label><br />
        <select name="status">
          <option>accept</option>
          <option>edit</option>
          <option>needs more evidence</option>
          <option>reject</option>
        </select>
        <input name="note" placeholder="optional note" />
        <button type="submit">Save feedback</button>
      </form>
    """
    return f"""
    <article class="card">
      <h2>Theme {index}: {html.escape(theme.title)}</h2>
      <p><span class="badge"><strong>confidence</strong> {html.escape(theme.confidence)}</span></p>
      <p><strong>Participants:</strong> {html.escape(', '.join(theme.participants))}</p>
      <p><strong>Finding:</strong> {html.escape(theme.finding)}</p>
      <details open>
        <summary>Evidence quotes</summary>
        <ul>{evidence_items}</ul>
      </details>
      <details open>
        <summary>Claim-to-evidence map</summary>
        {claim_blocks}
      </details>
      <p><strong>Opportunity:</strong> {html.escape(theme.product_opportunity)}</p>
      <p><strong>Risk:</strong> {html.escape(theme.risk_if_ignored)}</p>
      <p><strong>Next question:</strong> {html.escape(theme.next_question)}</p>
      {feedback_form}
    </article>
    """


def _render_claim_html(claim: InsightClaim) -> str:
    evidence_items = "\n".join(f"<li>{_format_evidence_html(e)}</li>" for e in claim.evidence)
    return f"""
    <div class="claim">
      <p><strong>Claim:</strong> {html.escape(claim.claim)}</p>
      <p><strong>Why it matters:</strong> {html.escape(claim.why_it_matters)}</p>
      <ul>{evidence_items}</ul>
    </div>
    """


def _format_evidence(evidence: Evidence) -> str:
    evidence_id = f"{evidence.evidence_id}: " if evidence.evidence_id else ""
    return (
        f"{evidence_id}\"{evidence.quote}\" — "
        f"{evidence.participant_id}, {evidence.timestamp} (`{evidence.source_file}`)"
    )


def _format_evidence_html(evidence: Evidence) -> str:
    evidence_id = f"{html.escape(evidence.evidence_id)}: " if evidence.evidence_id else ""
    return (
        f'<div class="quote">{evidence_id}“{html.escape(evidence.quote)}”<br />'
        f'<span class="muted">{html.escape(evidence.participant_id)}, '
        f'{html.escape(evidence.timestamp)} · {html.escape(evidence.source_file)}</span></div>'
    )


def _escape_table(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")
