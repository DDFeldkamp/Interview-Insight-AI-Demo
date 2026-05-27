from __future__ import annotations

from .models import ResearchBrief, TranscriptChunk
from .text import tokenize


def evaluate_brief(brief: ResearchBrief, chunks: list[TranscriptChunk]) -> dict[str, float]:
    corpus = "\n".join(chunk.text for chunk in chunks).lower()
    all_quotes = [e.quote for theme in brief.themes for e in theme.evidence] + [
        e.quote for theme in brief.themes for claim in theme.claims for e in claim.evidence
    ] + [e.quote for e in brief.surprising_quotes]
    grounded = sum(1 for quote in all_quotes if _quote_is_grounded(quote, corpus))
    groundedness = grounded / max(1, len(all_quotes))

    cited_participants = {e.participant_id for theme in brief.themes for e in theme.evidence}
    total_participants = {chunk.participant.participant_id for chunk in chunks}
    source_coverage = len(cited_participants) / max(1, len(total_participants))

    theme_texts = [theme.finding + " " + theme.product_opportunity for theme in brief.themes]
    redundancy = _average_pairwise_jaccard(theme_texts)

    claims = [claim for theme in brief.themes for claim in theme.claims]
    claims_with_evidence = sum(1 for claim in claims if claim.evidence)
    claim_evidence_coverage = claims_with_evidence / max(1, len(claims))

    multi_source_themes = sum(1 for theme in brief.themes if len({e.participant_id for e in theme.evidence}) >= 2)
    multi_source_theme_rate = multi_source_themes / max(1, len(brief.themes))

    return {
        "groundedness": round(groundedness, 3),
        "source_coverage": round(source_coverage, 3),
        "theme_redundancy": round(redundancy, 3),
        "claim_evidence_coverage": round(claim_evidence_coverage, 3),
        "multi_source_theme_rate": round(multi_source_theme_rate, 3),
    }


def _quote_is_grounded(quote: str, corpus: str) -> bool:
    normalized = quote.lower().strip().strip('"')
    if normalized in corpus:
        return True
    quote_tokens = tokenize(normalized)
    if len(quote_tokens) < 5:
        return False
    corpus_tokens = set(tokenize(corpus))
    overlap = sum(1 for token in quote_tokens if token in corpus_tokens) / len(quote_tokens)
    return overlap >= 0.8


def _average_pairwise_jaccard(texts: list[str]) -> float:
    if len(texts) < 2:
        return 0.0
    scores: list[float] = []
    token_sets = [set(tokenize(text)) for text in texts]
    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            if not left and not right:
                scores.append(1.0)
            else:
                scores.append(len(left & right) / max(1, len(left | right)))
    return sum(scores) / len(scores)
