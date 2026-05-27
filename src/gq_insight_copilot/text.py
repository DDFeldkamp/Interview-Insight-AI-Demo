from __future__ import annotations

import math
import re
from collections import Counter
from typing import Optional
from dataclasses import dataclass

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]{2,}")

STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before",
    "being", "between", "both", "but", "can", "could", "did", "does", "doing", "for",
    "from", "get", "had", "has", "have", "her", "here", "him", "his", "how", "into",
    "just", "like", "more", "most", "need", "not", "now", "our", "out", "over", "really",
    "she", "should", "some", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "through", "too", "use", "was", "way", "were", "what", "when",
    "where", "which", "who", "why", "with", "would", "you", "your", "interviewer", "participant",
}

POSITIVE_WORDS = {
    "clear", "confident", "easy", "fast", "helpful", "love", "saved", "simple", "trusted",
}
NEGATIVE_WORDS = {
    "confusing", "hard", "manual", "messy", "pain", "slow", "stuck", "waste", "lost",
    "blocked", "fragile", "annoying", "worried", "risk", "missing", "inconsistent",
}

DOMAIN_TAGS: dict[str, set[str]] = {
    "recruiting": {"recruit", "participant", "panel", "screen", "screener", "schedule", "incentive"},
    "analysis": {"analyze", "summary", "summaries", "theme", "themes", "cluster", "quote", "quotes"},
    "repository": {"repository", "source", "evidence", "decision", "share", "insight", "report"},
    "trust": {"trust", "confidence", "grounded", "citation", "source", "defend", "audit"},
    "workflow": {"workflow", "handoff", "roadmap", "product", "pm", "designer", "researcher"},
}


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS]


def extract_keywords(text: str, *, top_k: int = 8) -> list[str]:
    counts = Counter(tokenize(text))
    return [word for word, _ in counts.most_common(top_k)]


def classify_tags(text: str) -> list[str]:
    tokens = set(tokenize(text))
    tags = [name for name, vocab in DOMAIN_TAGS.items() if tokens & vocab]
    return tags or ["general"]


def sentiment_score(text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    positives = sum(1 for token in tokens if token in POSITIVE_WORDS)
    negatives = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    return (positives - negatives) / math.sqrt(len(tokens))


def readable_label(tag: str) -> str:
    labels = {
        "recruiting": "Recruiting and scheduling create hidden drag",
        "analysis": "Analysis needs speed without flattening nuance",
        "repository": "Research handoff is too lossy",
        "trust": "AI summaries need visible evidence trails",
        "workflow": "Insights must land inside product workflows",
        "general": "Repeated friction across the research workflow",
    }
    return labels.get(tag, tag.replace("_", " ").title())


@dataclass(frozen=True)
class Sentence:
    text: str
    score: float


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 12]


def best_sentence(text: str, query_terms: Optional[set[str]] = None) -> str:
    query_terms = query_terms or set()
    candidates: list[Sentence] = []
    for sentence in split_sentences(text):
        tokens = set(tokenize(sentence))
        domain_hit = sum(1 for vocab in DOMAIN_TAGS.values() if tokens & vocab)
        query_hit = len(tokens & query_terms)
        emotion = abs(sentiment_score(sentence))
        score = 0.7 * query_hit + 0.5 * domain_hit + emotion + min(len(sentence) / 250, 0.5)
        candidates.append(Sentence(sentence, score))
    if not candidates:
        return text.strip()[:240]
    return max(candidates, key=lambda item: item.score).text
