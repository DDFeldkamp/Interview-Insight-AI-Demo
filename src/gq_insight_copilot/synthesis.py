from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from typing import Optional
from pathlib import Path

from pydantic import ValidationError

from .evaluation import evaluate_brief
from .ingest import chunk_turns, load_transcripts
from .llm import get_client
from .models import Evidence, InsightClaim, ResearchBrief, RetrievalResult, Theme, TranscriptChunk
from .text import best_sentence, classify_tags, readable_label, tokenize
from .vector_store import OpenAIEmbeddingVectorStore, TfidfVectorStore


def synthesize_from_directory(
    input_dir: Path,
    *,
    objective: str,
    provider: str = "local",
    top_k: int = 14,
    retriever: str = "tfidf",
) -> ResearchBrief:
    """End-to-end research synthesis pipeline.

    The default path is deterministic so the repo works without API keys. The optional OpenAI
    path still uses the same retrieval, quote whitelist, Pydantic validation, and automated evals,
    so model output is treated as untrusted until checked.
    """

    parsed = load_transcripts(input_dir)
    chunks = chunk_turns(parsed)
    retrieved = retrieve_relevant_chunks(chunks, objective=objective, top_k=top_k, retriever=retriever)

    if provider == "openai":
        try:
            brief = synthesize_with_llm(retrieved, objective=objective, chunks=chunks)
            brief.eval_scores = evaluate_brief(brief, chunks)
            return brief
        except Exception:
            # Application demos should not break when a key is missing or the model returns invalid JSON.
            # The fallback is visible in eval_scores so reviewers can see the behavior.
            brief = synthesize_locally(retrieved, objective=objective, chunks=chunks)
            brief.eval_scores["llm_fallback_used"] = 1.0
            return brief

    if provider != "local":
        raise ValueError(f"Unknown provider: {provider}")
    return synthesize_locally(retrieved, objective=objective, chunks=chunks)


def retrieve_relevant_chunks(
    chunks: list[TranscriptChunk], *, objective: str, top_k: int, retriever: str = "tfidf"
) -> list[RetrievalResult]:
    expanded_query = _expand_query(objective)
    if retriever == "tfidf":
        store = TfidfVectorStore.from_chunks(chunks)
    elif retriever == "embeddings":
        store = OpenAIEmbeddingVectorStore.from_chunks(chunks)
    else:
        raise ValueError("retriever must be 'tfidf' or 'embeddings'")

    retrieved = store.search(expanded_query, k=top_k)

    # Fall back to broad coverage if the objective is too sparse for retrieval.
    if len(retrieved) < min(5, len(chunks)):
        retrieved_ids = {item.chunk.chunk_id for item in retrieved}
        for chunk in chunks:
            if chunk.chunk_id not in retrieved_ids:
                retrieved.append(RetrievalResult(chunk=chunk, score=0.05))
            if len(retrieved) >= top_k:
                break
    return retrieved


def synthesize_locally(
    results: list[RetrievalResult], *, objective: str, chunks: list[TranscriptChunk]
) -> ResearchBrief:
    themes = build_themes(results, objective=objective)
    surprising_quotes = pick_surprising_quotes(results, limit=3)
    brief = ResearchBrief(
        objective=objective,
        executive_summary=make_executive_summary(themes, objective),
        themes=themes,
        surprising_quotes=surprising_quotes,
        recommended_next_steps=make_next_steps(themes),
    )
    brief.eval_scores = evaluate_brief(brief, chunks)
    return brief


def synthesize_with_llm(
    results: list[RetrievalResult], *, objective: str, chunks: list[TranscriptChunk]
) -> ResearchBrief:
    candidates = _candidate_evidence_from_results(results, objective=objective, limit=14)
    prompt = build_llm_prompt(objective=objective, candidates=candidates)
    response_text = get_client("openai").complete(prompt)
    brief = _parse_and_validate_llm_brief(response_text, objective=objective, candidates=candidates)
    brief = _repair_and_complete_brief(brief, candidates=candidates, objective=objective)
    if not brief.themes:
        raise ValueError("LLM returned no themes")
    if not any(theme.evidence for theme in brief.themes):
        raise ValueError("LLM returned no grounded evidence")
    brief.eval_scores = evaluate_brief(brief, chunks)
    return brief


def build_llm_prompt(*, objective: str, candidates: list[Evidence]) -> str:
    evidence_lines = []
    for item in candidates:
        tags = ", ".join(item.tags) if item.tags else "general"
        evidence_lines.append(
            f"- {item.evidence_id}: participant={item.participant_id}; "
            f"timestamp={item.timestamp}; source={item.source_file}; tags={tags}; quote=\"{item.quote}\""
        )

    return f"""
You are helping synthesize customer research for a product team.

Research objective:
{objective}

Evidence candidates you may use:
{chr(10).join(evidence_lines)}

Rules:
1. Return ONLY valid JSON. No Markdown and no prose outside JSON.
2. Every evidence quote in your answer must be copied exactly from the evidence candidates.
3. Every theme must have 1-3 claim-to-evidence objects in `claims`.
4. Do not invent participants, timestamps, source files, or quotes.
5. Prefer specific, decision-oriented findings over generic summaries.

Return this JSON shape:
{{
  "objective": "{objective}",
  "executive_summary": "2-4 sentences summarizing the strongest research signal and product implication.",
  "themes": [
    {{
      "title": "short theme title",
      "finding": "one sentence finding grounded in evidence",
      "confidence": "low|medium|high",
      "participants": ["P01", "P02"],
      "evidence": [
        {{
          "evidence_id": "E01",
          "participant_id": "P01",
          "quote": "exact quote from candidates",
          "timestamp": "00:00:00",
          "source_file": "file.md",
          "relevance": 0.9,
          "tags": ["trust"]
        }}
      ],
      "claims": [
        {{
          "claim": "specific claim supported by the evidence",
          "why_it_matters": "why this should affect a product or research decision",
          "evidence": [
            {{
              "evidence_id": "E01",
              "participant_id": "P01",
              "quote": "exact quote from candidates",
              "timestamp": "00:00:00",
              "source_file": "file.md",
              "relevance": 0.9,
              "tags": ["trust"]
            }}
          ]
        }}
      ],
      "product_opportunity": "what Great Question-like product capability this suggests",
      "risk_if_ignored": "what happens if the workflow stays the same",
      "next_question": "next research question to ask"
    }}
  ],
  "surprising_quotes": [],
  "recommended_next_steps": []
}}
""".strip()


def build_themes(results: list[RetrievalResult], *, objective: str) -> list[Theme]:
    grouped: dict[str, list[RetrievalResult]] = defaultdict(list)
    for result in results:
        tags = classify_tags(result.chunk.text)
        primary = _select_primary_tag(tags, objective)
        grouped[primary].append(result)

    themes: list[Theme] = []
    for tag, group in sorted(grouped.items(), key=lambda item: _group_strength(item[1]), reverse=True):
        evidence = _dedupe_evidence([_evidence_from_result(item, objective) for item in group], limit=4)
        participants = sorted({item.participant_id for item in evidence})
        if not evidence:
            continue
        theme = Theme(
            title=readable_label(tag),
            finding=_finding_for_tag(tag, evidence),
            confidence=_confidence(len(participants), len(evidence), sum(r.score for r in group)),
            participants=participants,
            evidence=evidence,
            product_opportunity=_opportunity_for_tag(tag),
            risk_if_ignored=_risk_for_tag(tag),
            next_question=_next_question_for_tag(tag),
        )
        theme.claims = [_claim_for_theme(tag, evidence)]
        themes.append(theme)
    return themes[:5]


def _select_primary_tag(tags: list[str], objective: str) -> str:
    objective_tokens = set(tokenize(objective))
    if "trust" in tags and {"evidence", "source", "trust", "citation"} & objective_tokens:
        return "trust"
    if "repository" in tags and {"repository", "share", "handoff", "decision"} & objective_tokens:
        return "repository"
    priority = ["analysis", "repository", "workflow", "trust", "recruiting", "general"]
    return min(tags, key=lambda tag: priority.index(tag) if tag in priority else 99)


def _group_strength(group: list[RetrievalResult]) -> float:
    return sum(item.score for item in group) + 0.15 * len({item.chunk.participant.participant_id for item in group})


def _evidence_from_result(result: RetrievalResult, objective: str) -> Evidence:
    query_terms = set(tokenize(objective)) | set(result.chunk.keywords[:5])
    quote, timestamp = _best_participant_quote(result.chunk, query_terms)
    return Evidence(
        participant_id=result.chunk.participant.participant_id,
        quote=quote,
        timestamp=timestamp,
        source_file=result.chunk.source_file,
        relevance=min(1.0, max(0.05, result.score)),
        tags=classify_tags(result.chunk.text),
    )


def _best_participant_quote(chunk: TranscriptChunk, query_terms: set[str]) -> tuple[str, str]:
    participant_turns = [turn for turn in chunk.turns if turn.speaker == "Participant"]
    if not participant_turns:
        quote = best_sentence(chunk.text, query_terms=query_terms)
        return quote.removeprefix("Participant: ").removeprefix("Interviewer: ").strip(), chunk.start_timestamp

    best_turn = max(
        participant_turns,
        key=lambda turn: (
            len(set(tokenize(turn.text)) & query_terms),
            len(set(classify_tags(turn.text))),
            min(len(turn.text), 240),
        ),
    )
    return best_sentence(best_turn.text, query_terms=query_terms), best_turn.timestamp


def _dedupe_evidence(evidence: list[Evidence], *, limit: int) -> list[Evidence]:
    seen_quotes: set[str] = set()
    seen_participant_quote: set[tuple[str, str]] = set()
    unique: list[Evidence] = []
    for item in sorted(evidence, key=lambda e: e.relevance, reverse=True):
        quote_key = " ".join(tokenize(item.quote))
        participant_key = (item.participant_id, quote_key)
        if quote_key in seen_quotes or participant_key in seen_participant_quote:
            continue
        seen_quotes.add(quote_key)
        seen_participant_quote.add(participant_key)
        unique.append(item)
        if len(unique) >= limit:
            break
    return unique


def _candidate_evidence_from_results(
    results: list[RetrievalResult], *, objective: str, limit: int
) -> list[Evidence]:
    raw = [_evidence_from_result(result, objective) for result in results]
    unique = _dedupe_evidence(raw, limit=limit)
    for index, evidence in enumerate(unique, start=1):
        evidence.evidence_id = f"E{index:02d}"
    return unique


def _parse_and_validate_llm_brief(text: str, *, objective: str, candidates: list[Evidence]) -> ResearchBrief:
    try:
        payload = json.loads(_extract_json_object(text))
    except json.JSONDecodeError as exc:
        raise ValueError("LLM did not return valid JSON") from exc

    payload.setdefault("objective", objective)
    payload.setdefault("themes", [])
    payload.setdefault("surprising_quotes", [])
    payload.setdefault("recommended_next_steps", [])
    try:
        return ResearchBrief.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("LLM JSON did not match the ResearchBrief schema") from exc


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", stripped, 0)
    return stripped[start : end + 1]


def _repair_and_complete_brief(
    brief: ResearchBrief, *, candidates: list[Evidence], objective: str
) -> ResearchBrief:
    id_lookup = {item.evidence_id: item for item in candidates if item.evidence_id}
    quote_lookup = {_normalize_quote(item.quote): item for item in candidates}
    timestamp_lookup = {(item.participant_id, item.timestamp): item for item in candidates}

    def repair_evidence(item: Evidence) -> Optional[Evidence]:
        if item.evidence_id and item.evidence_id in id_lookup:
            return id_lookup[item.evidence_id]
        quote_match = quote_lookup.get(_normalize_quote(item.quote))
        if quote_match is not None:
            return quote_match
        timestamp_match = timestamp_lookup.get((item.participant_id, item.timestamp))
        if timestamp_match is not None:
            return timestamp_match
        return None

    repaired_themes: list[Theme] = []
    for theme in brief.themes:
        repaired_evidence = [item for item in (repair_evidence(e) for e in theme.evidence) if item]
        theme.evidence = _dedupe_evidence(repaired_evidence, limit=4)
        theme.participants = sorted({e.participant_id for e in theme.evidence}) or theme.participants

        repaired_claims: list[InsightClaim] = []
        for claim in theme.claims:
            claim_evidence = [item for item in (repair_evidence(e) for e in claim.evidence) if item]
            claim.evidence = _dedupe_evidence(claim_evidence, limit=3)
            if claim.evidence:
                repaired_claims.append(claim)
        if not repaired_claims and theme.evidence:
            repaired_claims.append(_claim_for_theme("general", theme.evidence))
        theme.claims = repaired_claims
        if theme.evidence:
            repaired_themes.append(theme)

    brief.themes = repaired_themes
    brief.surprising_quotes = [
        item for item in (repair_evidence(e) for e in brief.surprising_quotes) if item
    ][:3]
    if not brief.surprising_quotes:
        brief.surprising_quotes = candidates[:3]
    if not brief.recommended_next_steps:
        brief.recommended_next_steps = make_next_steps(brief.themes)
    if not brief.executive_summary:
        brief.executive_summary = make_executive_summary(brief.themes, objective)
    return brief


def _normalize_quote(text: str) -> str:
    return " ".join(tokenize(text))


def _claim_for_theme(tag: str, evidence: list[Evidence]) -> InsightClaim:
    claim_templates = {
        "recruiting": "Study setup delays are not just logistics; they change how quickly teams can learn.",
        "analysis": "Teams want AI to accelerate the first synthesis pass while preserving nuance.",
        "repository": "Research only stays valuable when teams can rediscover the decision and source evidence later.",
        "trust": "AI summaries become useful for decisions only when each claim can be audited against source quotes.",
        "workflow": "Insights need to travel into roadmap and planning workflows, not stop at a report.",
        "general": "The strongest product opportunity is to connect raw customer evidence to trusted decisions.",
    }
    why_templates = {
        "recruiting": "Reducing launch friction lets teams run more frequent, better targeted studies.",
        "analysis": "Researchers still need control, but a structured draft shortens time from calls to insight.",
        "repository": "A living evidence trail prevents old learning from disappearing into decks and docs.",
        "trust": "Stakeholders are more likely to act when they can inspect who said what and in what context.",
        "workflow": "A synthesis tool creates more value when it changes what the team builds next.",
        "general": "The product should make customer evidence easier to trust, reuse, and act on.",
    }
    return InsightClaim(
        claim=claim_templates.get(tag, claim_templates["general"]),
        why_it_matters=why_templates.get(tag, why_templates["general"]),
        evidence=evidence[:3],
    )


def pick_surprising_quotes(results: list[RetrievalResult], *, limit: int) -> list[Evidence]:
    scored = sorted(
        results,
        key=lambda item: (
            len(set(classify_tags(item.chunk.text))),
            abs(_lexical_tension(item.chunk.text)),
            item.score,
        ),
        reverse=True,
    )
    seen: set[str] = set()
    quotes: list[Evidence] = []
    for result in scored:
        evidence = _evidence_from_result(result, "surprising quote customer research")
        key = evidence.quote.lower()
        if key in seen:
            continue
        seen.add(key)
        quotes.append(evidence)
        if len(quotes) >= limit:
            break
    return quotes


def make_executive_summary(themes: list[Theme], objective: str) -> str:
    if not themes:
        return f"No strong themes were found for: {objective}"
    top = themes[0]
    participant_count = len({p for theme in themes for p in theme.participants})
    return (
        f"Across {participant_count} participants, the strongest signal is: {top.finding} "
        f"The main product implication is to reduce the gap between raw research data and "
        f"trusted, source-backed product decisions."
    )


def make_next_steps(themes: list[Theme]) -> list[str]:
    base_steps = [
        "Prototype insight cards that pair one-sentence findings with clickable quote evidence.",
        "Add a researcher review step so AI output is fast but still accountable.",
    ]
    tag_counts = Counter(tag for theme in themes for evidence in theme.evidence for tag in evidence.tags)
    if tag_counts.get("recruiting", 0) >= 2:
        base_steps.append("Test whether recruiting and screener automation shortens study setup time.")
    if tag_counts.get("trust", 0) >= 2:
        base_steps.append("Expose confidence, source coverage, and quote diversity on each generated summary.")
    if tag_counts.get("workflow", 0) >= 2:
        base_steps.append("Pilot integrations that push synthesized insights into planning docs or issue trackers.")
    return base_steps[:5]


def _finding_for_tag(tag: str, evidence: list[Evidence]) -> str:
    participants = ", ".join(sorted({e.participant_id for e in evidence}))
    findings = {
        "recruiting": f"Participants {participants} describe setup work before the interview as a major source of delay.",
        "analysis": f"Participants {participants} want faster synthesis, but not at the cost of nuance or traceability.",
        "repository": f"Participants {participants} need research outputs that are easy to reuse after the study ends.",
        "trust": f"Participants {participants} trust AI summaries only when the evidence trail is visible.",
        "workflow": f"Participants {participants} want insights to connect directly to roadmap and product workflows.",
        "general": f"Participants {participants} repeat friction that spans recruiting, synthesis, and sharing.",
    }
    return findings.get(tag, findings["general"])


def _opportunity_for_tag(tag: str) -> str:
    opportunities = {
        "recruiting": "Suggest participant segments, draft screeners, and flag scheduling bottlenecks before launch.",
        "analysis": "Generate editable thematic summaries with explicit quote clusters instead of opaque paragraphs.",
        "repository": "Create durable insight cards that preserve source context and can be rediscovered later.",
        "trust": "Attach citations, confidence signals, and source coverage metrics to each AI-generated claim.",
        "workflow": "Push research-backed recommendations into planning rituals where product decisions happen.",
        "general": "Unify study setup, analysis, and sharing so teams do not lose context between tools.",
    }
    return opportunities.get(tag, opportunities["general"])


def _risk_for_tag(tag: str) -> str:
    risks = {
        "recruiting": "Teams run fewer studies because coordination overhead remains too high.",
        "analysis": "Researchers reject summaries that feel fast but shallow.",
        "repository": "Insights disappear into old decks and are not reused in future decisions.",
        "trust": "Stakeholders dismiss AI output as unsupported opinion.",
        "workflow": "Good research arrives too late or too disconnected to influence roadmap choices.",
        "general": "The product is seen as another research storage tool rather than a decision accelerator.",
    }
    return risks.get(tag, risks["general"])


def _next_question_for_tag(tag: str) -> str:
    questions = {
        "recruiting": "Which part of recruiting feels most automatable without reducing participant quality?",
        "analysis": "What level of summary compression still preserves the nuance researchers need?",
        "repository": "When do teams search old research, and what metadata helps them trust what they find?",
        "trust": "What confidence indicators make AI-generated research findings feel auditable?",
        "workflow": "Where should an insight appear so it changes a product decision instead of becoming documentation?",
        "general": "Which research workflow step creates the highest cost when it breaks?",
    }
    return questions.get(tag, questions["general"])


def _confidence(participant_count: int, evidence_count: int, score_sum: float) -> str:
    if participant_count >= 3 and evidence_count >= 3 and score_sum > 0.6:
        return "high"
    if participant_count >= 2 and evidence_count >= 2:
        return "medium"
    return "low"


def _expand_query(objective: str) -> str:
    return (
        objective
        + " customer research interview study insights summary quotes repository trust workflow recruiting"
    )


def _lexical_tension(text: str) -> float:
    tokens = set(tokenize(text))
    positive = len(tokens & {"easy", "helpful", "love", "trusted", "fast"})
    negative = len(tokens & {"hard", "manual", "confusing", "slow", "risk", "lost"})
    return float(positive - negative)
