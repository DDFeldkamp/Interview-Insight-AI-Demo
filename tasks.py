"""Cross-platform task runner for Interview Insight Copilot.

Use this instead of `make` on Windows:

    python tasks.py demo
    python tasks.py test
    python tasks.py eval
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent


def run(args: list[str], *, with_pythonpath: bool = False) -> None:
    env = os.environ.copy()
    if with_pythonpath:
        existing = env.get("PYTHONPATH")
        src = str(ROOT / "src")
        env["PYTHONPATH"] = src if not existing else src + os.pathsep + existing
    print("$", " ".join(args))
    subprocess.run(args, cwd=ROOT, env=env, check=True)



def ensure_python_version() -> None:
    if sys.version_info < (3, 9):
        raise SystemExit(
            "Python 3.9 or newer is required. Install Python 3.11 from python.org if possible."
        )


def ensure_core_dependencies() -> None:
    """Install the small core dependency set if the user skipped setup."""
    try:
        import dotenv  # noqa: F401
        import pydantic  # noqa: F401
    except ModuleNotFoundError:
        print(
            "Core dependencies are missing. Installing the pinned minimal set with `pip install -e .`..."
        )
        install()


def install(extra: Optional[str] = None) -> None:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    package = "." if extra is None else f".[{extra}]"
    run([sys.executable, "-m", "pip", "install", "-e", package])


def demo() -> None:
    ensure_python_version()
    ensure_core_dependencies()
    run(
        [
            sys.executable,
            "-m",
            "gq_insight_copilot.cli",
            "synthesize",
            "--input",
            "sample_data/interviews",
            "--objective",
            "Find onboarding and research-repository friction for product managers",
            "--out",
            "outputs/demo_report.md",
            "--json",
        ],
        with_pythonpath=True,
    )


def openai_demo() -> None:
    ensure_python_version()
    ensure_core_dependencies()
    run(
        [
            sys.executable,
            "-m",
            "gq_insight_copilot.cli",
            "synthesize",
            "--input",
            "sample_data/interviews",
            "--objective",
            "What should we improve in the research workflow?",
            "--provider",
            "openai",
            "--out",
            "outputs/openai_report.md",
            "--json",
        ],
        with_pythonpath=True,
    )


def evaluate() -> None:
    ensure_python_version()
    ensure_core_dependencies()
    run(
        [
            sys.executable,
            "-m",
            "gq_insight_copilot.cli",
            "evaluate",
            "--cases",
            "eval/eval_cases.json",
            "--out",
            "outputs/eval_results.json",
        ],
        with_pythonpath=True,
    )


def test() -> None:
    ensure_python_version()
    run([sys.executable, "-m", "pytest", "-q"], with_pythonpath=True)


def serve() -> None:
    ensure_python_version()
    ensure_core_dependencies()
    run([sys.executable, "-m", "uvicorn", "gq_insight_copilot.api:app", "--reload"], with_pythonpath=True)


def clean() -> None:
    patterns = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "outputs",
        "build",
        "dist",
    ]
    for path in ROOT.rglob("*"):
        if path.is_dir() and path.name in patterns:
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and path.suffix == ".pyc":
            path.unlink(missing_ok=True)
    for path in list(ROOT.glob("*.egg-info")) + list((ROOT / "src").glob("*.egg-info")):
        shutil.rmtree(path, ignore_errors=True)
    print("Cleaned generated files.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-platform replacement for Makefile commands")
    parser.add_argument(
        "command",
        choices=[
            "install",
            "install-dev",
            "install-api",
            "install-llm",
            "install-all",
            "demo",
            "openai-demo",
            "eval",
            "test",
            "serve",
            "clean",
        ],
    )
    args = parser.parse_args()
    ensure_python_version()

    if args.command == "install":
        install()
    elif args.command == "install-dev":
        install("dev")
    elif args.command == "install-api":
        install("api")
    elif args.command == "install-llm":
        install("llm")
    elif args.command == "install-all":
        install("all")
    elif args.command == "demo":
        demo()
    elif args.command == "openai-demo":
        openai_demo()
    elif args.command == "eval":
        evaluate()
    elif args.command == "test":
        test()
    elif args.command == "serve":
        serve()
    elif args.command == "clean":
        clean()


if __name__ == "__main__":
    main()
