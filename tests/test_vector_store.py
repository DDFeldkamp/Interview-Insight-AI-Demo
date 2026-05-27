from pathlib import Path

from gq_insight_copilot.ingest import chunk_turns, load_transcripts
from gq_insight_copilot.vector_store import TfidfVectorStore


def test_vector_store_retrieves_source_grounding_chunks() -> None:
    chunks = chunk_turns(load_transcripts(Path("sample_data/interviews")))
    store = TfidfVectorStore.from_chunks(chunks)
    results = store.search("AI summaries need source quotes and confidence", k=5)

    assert results
    assert results[0].score > 0
    assert any("source" in result.chunk.text.lower() for result in results)
