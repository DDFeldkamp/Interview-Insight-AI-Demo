from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from typing import Iterable

from .models import Participant, TranscriptChunk, TranscriptTurn
from .text import extract_keywords

META_RE = re.compile(r"^---\n(?P<meta>.*?)\n---\n(?P<body>.*)$", re.DOTALL)
TURN_RE = re.compile(
    r"^\[(?P<time>\d{2}:\d{2}:\d{2})\]\s+(?P<speaker>Interviewer|Participant):\s+(?P<text>.*)$"
)


def _parse_meta(raw_meta: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta


def parse_transcript(path: Path) -> tuple[Participant, list[TranscriptTurn]]:
    """Parse a markdown transcript with YAML-ish front matter.

    This parser is deliberately small and dependency-light for demo reliability.
    """

    raw = path.read_text(encoding="utf-8")
    match = META_RE.match(raw)
    if not match:
        raise ValueError(f"{path} is missing front matter")

    meta = _parse_meta(match.group("meta"))
    participant = Participant(
        participant_id=meta.get("participant_id", path.stem),
        role=meta.get("role", "unknown"),
        company_size=meta.get("company_size", "unknown"),
        research_maturity=meta.get("research_maturity", "unknown"),
    )

    turns: list[TranscriptTurn] = []
    current: Optional[TranscriptTurn] = None

    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        turn_match = TURN_RE.match(line)
        if turn_match:
            if current is not None:
                turns.append(current)
            current = TranscriptTurn(
                participant_id=participant.participant_id,
                timestamp=turn_match.group("time"),
                speaker=turn_match.group("speaker"),
                text=turn_match.group("text").strip(),
                source_file=path.name,
            )
        elif current is not None:
            current.text += " " + line

    if current is not None:
        turns.append(current)

    return participant, turns


def load_transcripts(input_dir: Path) -> list[tuple[Participant, list[TranscriptTurn]]]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    paths = sorted(input_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No .md transcripts found in {input_dir}")
    return [parse_transcript(path) for path in paths]


def chunk_turns(
    parsed: Iterable[tuple[Participant, list[TranscriptTurn]]],
    *,
    max_turns_per_chunk: int = 4,
) -> list[TranscriptChunk]:
    """Group interview turns into retrieval chunks.

    We keep interviewer context because the same participant answer can mean different things
    depending on the research prompt that preceded it.
    """

    chunks: list[TranscriptChunk] = []
    for participant, turns in parsed:
        window: list[TranscriptTurn] = []
        chunk_index = 0
        for turn in turns:
            window.append(turn)
            if len(window) >= max_turns_per_chunk:
                chunks.append(_make_chunk(participant, window, chunk_index))
                chunk_index += 1
                window = window[-1:]  # overlap one turn for continuity
        if window:
            chunks.append(_make_chunk(participant, window, chunk_index))
    return chunks


def _make_chunk(participant: Participant, turns: list[TranscriptTurn], chunk_index: int) -> TranscriptChunk:
    text = "\n".join(f"{turn.speaker}: {turn.text}" for turn in turns)
    return TranscriptChunk(
        chunk_id=f"{participant.participant_id}-{chunk_index:03d}",
        participant=participant,
        text=text,
        source_file=turns[0].source_file,
        start_timestamp=turns[0].timestamp,
        end_timestamp=turns[-1].timestamp,
        turns=list(turns),
        keywords=extract_keywords(text, top_k=8),
    )
