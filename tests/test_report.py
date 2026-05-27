from pathlib import Path

from gq_insight_copilot.report import render_markdown
from gq_insight_copilot.synthesis import synthesize_from_directory


def test_report_contains_expected_sections() -> None:
    brief = synthesize_from_directory(
        Path("sample_data/interviews"),
        objective="What research repository features matter most?",
    )
    markdown = render_markdown(brief)

    assert "# AI Research Brief" in markdown
    assert "## Themes" in markdown
    assert "## Claim-to-evidence map" in markdown
    assert "## Automated eval checks" in markdown
    assert "Product opportunity" in markdown
    assert "Claim:" in markdown
