from pathlib import Path

from gq_insight_copilot.synthesis import synthesize_from_directory


def test_synthesis_generates_grounded_brief() -> None:
    brief = synthesize_from_directory(
        Path("sample_data/interviews"),
        objective="Find trust issues in AI-generated interview summaries",
    )

    assert brief.themes
    assert brief.eval_scores["groundedness"] >= 0.9
    assert brief.eval_scores["source_coverage"] >= 0.4
    assert any(theme.evidence for theme in brief.themes)
