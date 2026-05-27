from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .eval_runner import run_eval_file
from .report import render_markdown
from .synthesis import synthesize_from_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthesize customer interviews into a research brief")
    subparsers = parser.add_subparsers(dest="command", required=True)

    synthesize = subparsers.add_parser("synthesize", help="Generate an AI research brief")
    synthesize.add_argument("--input", type=Path, required=True, help="Directory of transcript .md files")
    synthesize.add_argument("--objective", required=True, help="Research objective or question")
    synthesize.add_argument("--out", type=Path, default=Path("outputs/demo_report.md"))
    synthesize.add_argument("--provider", choices=["local", "openai"], default="local")
    synthesize.add_argument("--retriever", choices=["tfidf", "embeddings"], default="tfidf")
    synthesize.add_argument("--json", action="store_true", help="Also write structured JSON next to markdown")

    evaluate = subparsers.add_parser("evaluate", help="Run lightweight AI quality evals")
    evaluate.add_argument("--cases", type=Path, default=Path("eval/eval_cases.json"))
    evaluate.add_argument("--out", type=Path, default=Path("outputs/eval_results.json"))
    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "synthesize":
        brief = synthesize_from_directory(
            args.input,
            objective=args.objective,
            provider=args.provider,
            retriever=args.retriever,
        )
        markdown = render_markdown(brief)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(markdown, encoding="utf-8")
        if args.json:
            args.out.with_suffix(".json").write_text(
                json.dumps(brief.model_dump(), indent=2), encoding="utf-8"
            )
        print(f"Wrote {args.out}")
        print(f"Groundedness: {brief.eval_scores.get('groundedness', 0):.3f}")
        print(f"Claim evidence coverage: {brief.eval_scores.get('claim_evidence_coverage', 0):.3f}")
    elif args.command == "evaluate":
        summary = run_eval_file(args.cases, out_path=args.out)
        print(f"Wrote {args.out}")
        print(f"Passed: {summary['passed']} | Failed: {summary['failed']}")
        if summary["failed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
