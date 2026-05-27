from pathlib import Path

from gq_insight_copilot.eval_runner import run_eval_file


def test_eval_runner_passes_sample_cases(tmp_path: Path) -> None:
    out = tmp_path / "eval_results.json"
    summary = run_eval_file(Path("eval/eval_cases.json"), out_path=out)

    assert out.exists()
    assert summary["failed"] == 0
    assert summary["passed"] >= 1
