from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


class Participant(BaseModel):
    participant_id: str
    role: str = "unknown"
    company_size: str = "unknown"
    research_maturity: str = "unknown"


class TranscriptTurn(BaseModel):
    participant_id: str
    timestamp: str
    speaker: str
    text: str
    source_file: str


class Evidence(BaseModel):
    participant_id: str
    quote: str
    timestamp: str
    source_file: str
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    evidence_id: Optional[str] = None

    @property
    def citation(self) -> str:
        return f"{self.participant_id}, {self.timestamp}, {self.source_file}"


class InsightClaim(BaseModel):
    claim: str
    why_it_matters: str
    evidence: list[Evidence] = Field(default_factory=list)


class TranscriptChunk(BaseModel):
    chunk_id: str
    participant: Participant
    text: str
    source_file: str
    start_timestamp: str
    end_timestamp: str
    turns: list[TranscriptTurn] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class Theme(BaseModel):
    title: str
    finding: str
    confidence: str
    participants: list[str]
    evidence: list[Evidence]
    product_opportunity: str
    risk_if_ignored: str
    next_question: str
    claims: list[InsightClaim] = Field(default_factory=list)


class ResearchBrief(BaseModel):
    objective: str
    executive_summary: str
    themes: list[Theme]
    surprising_quotes: list[Evidence]
    recommended_next_steps: list[str]
    eval_scores: dict[str, float] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    chunk: TranscriptChunk
    score: float
