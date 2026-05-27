from pathlib import Path

from gq_insight_copilot.ingest import chunk_turns, load_transcripts, parse_transcript


def test_parse_transcript_extracts_metadata_and_turns() -> None:
    participant, turns = parse_transcript(Path("sample_data/interviews/P01_product_manager.md"))

    assert participant.participant_id == "P01"
    assert participant.role == "Product Manager"
    assert len(turns) >= 6
    assert turns[0].speaker == "Interviewer"
    assert turns[1].speaker == "Participant"


def test_chunk_turns_keeps_participant_context() -> None:
    parsed = load_transcripts(Path("sample_data/interviews"))
    chunks = chunk_turns(parsed, max_turns_per_chunk=4)

    assert chunks
    assert all(chunk.participant.participant_id.startswith("P") for chunk in chunks)
    assert any("roadmap" in chunk.text.lower() for chunk in chunks)
