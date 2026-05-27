from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .synthesis import synthesize_from_directory


def run_eval_file(cases_path: Path, *, out_path: Optional[Path] = None) -> dict[str, Any]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    results = [run_eval_case(case) for case in cases]
    summary = {
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "results": results,
    }
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_eval_case(case: dict[str, Any]) -> dict[str, Any]:
    objective = str(case["objective"])
    input_dir = Path(str(case["input_dir"]))
    provider = str(case.get("provider", "local"))
    retriever = str(case.get("retriever", "tfidf"))
    expectations = dict(case.get("expectations", {}))

    brief = synthesize_from_directory(
        input_dir,
        objective=objective,
        provider=provider,
        retriever=retriever,
    )
    checks = _evaluate_expectations(brief, expectations)
    return {
        "name": case.get("name", objective),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "eval_scores": brief.eval_scores,
        "theme_titles": [theme.title for theme in brief.themes],
    }


def _evaluate_expectations(brief: Any, expectations: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "actual": actual, "expected": expected})

    if "min_groundedness" in expectations:
        actual = brief.eval_scores.get("groundedness", 0.0)
        add("min_groundedness", actual >= expectations["min_groundedness"], actual, expectations["min_groundedness"])
    if "min_source_coverage" in expectations:
        actual = brief.eval_scores.get("source_coverage", 0.0)
        add("min_source_coverage", actual >= expectations["min_source_coverage"], actual, expectations["min_source_coverage"])
    if "max_theme_redundancy" in expectations:
        actual = brief.eval_scores.get("theme_redundancy", 1.0)
        add("max_theme_redundancy", actual <= expectations["max_theme_redundancy"], actual, expectations["max_theme_redundancy"])
    if "min_claim_evidence_coverage" in expectations:
        actual = brief.eval_scores.get("claim_evidence_coverage", 0.0)
        add(
            "min_claim_evidence_coverage",
            actual >= expectations["min_claim_evidence_coverage"],
            actual,
            expectations["min_claim_evidence_coverage"],
        )
    if "min_themes" in expectations:
        actual = len(brief.themes)
        add("min_themes", actual >= expectations["min_themes"], actual, expectations["min_themes"])
    if "required_terms" in expectations:
        report_parts = [brief.executive_summary]
        for theme in brief.themes:
            report_parts.extend(
                [
                    theme.title,
                    theme.finding,
                    theme.product_opportunity,
                    theme.risk_if_ignored,
                    theme.next_question,
                ]
            )
            report_parts.extend(evidence.quote for evidence in theme.evidence)
            for claim in theme.claims:
                report_parts.extend([claim.claim, claim.why_it_matters])
                report_parts.extend(evidence.quote for evidence in claim.evidence)
        report_parts.extend(brief.recommended_next_steps)
        report_text = " ".join(report_parts).lower()
        missing = [term for term in expectations["required_terms"] if term.lower() not in report_text]
        add("required_terms", not missing, {"missing": missing}, expectations["required_terms"])
    return checks
