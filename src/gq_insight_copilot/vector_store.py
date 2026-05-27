from __future__ import annotations

import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass

from .models import RetrievalResult, TranscriptChunk
from .text import tokenize

Vector = dict[str, float]
DenseVector = list[float]


@dataclass
class TfidfVectorStore:
    chunks: list[TranscriptChunk]
    idf: dict[str, float]
    vectors: dict[str, Vector]

    @classmethod
    def from_chunks(cls, chunks: list[TranscriptChunk]) -> "TfidfVectorStore":
        if not chunks:
            raise ValueError("Cannot build a vector store with zero chunks")

        doc_freq: dict[str, int] = defaultdict(int)
        tokenized: dict[str, list[str]] = {}
        for chunk in chunks:
            tokens = tokenize(chunk.text + " " + " ".join(chunk.keywords))
            tokenized[chunk.chunk_id] = tokens
            for token in set(tokens):
                doc_freq[token] += 1

        total_docs = len(chunks)
        idf = {token: math.log((1 + total_docs) / (1 + df)) + 1 for token, df in doc_freq.items()}
        vectors = {chunk_id: _tfidf(tokens, idf) for chunk_id, tokens in tokenized.items()}
        return cls(chunks=chunks, idf=idf, vectors=vectors)

    def search(self, query: str, *, k: int = 8) -> list[RetrievalResult]:
        query_vector = _tfidf(tokenize(query), self.idf)
        results: list[RetrievalResult] = []
        for chunk in self.chunks:
            score = cosine(query_vector, self.vectors[chunk.chunk_id])
            if score > 0:
                results.append(RetrievalResult(chunk=chunk, score=score))
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:k]


@dataclass
class OpenAIEmbeddingVectorStore:
    """Optional semantic retriever for the demo.

    TF-IDF is the default because it is deterministic and free. This class shows the upgrade path
    Great Question might use for deeper semantic matching when API access is available.
    """

    chunks: list[TranscriptChunk]
    vectors: dict[str, DenseVector]
    model: str = "text-embedding-3-small"

    @classmethod
    def from_chunks(
        cls, chunks: list[TranscriptChunk], *, model: str = "text-embedding-3-small"
    ) -> "OpenAIEmbeddingVectorStore":
        if not chunks:
            raise ValueError("Cannot build a vector store with zero chunks")
        vectors = _embed_texts([chunk.text for chunk in chunks], model=model)
        return cls(
            chunks=chunks,
            vectors={chunk.chunk_id: vector for chunk, vector in zip(chunks, vectors, strict=True)},
            model=model,
        )

    def search(self, query: str, *, k: int = 8) -> list[RetrievalResult]:
        query_vector = _embed_texts([query], model=self.model)[0]
        results = [
            RetrievalResult(chunk=chunk, score=dense_cosine(query_vector, self.vectors[chunk.chunk_id]))
            for chunk in self.chunks
        ]
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:k]


def _embed_texts(texts: list[str], *, model: str) -> list[DenseVector]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the llm extra: pip install -e '.[llm]'") from exc

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def _tfidf(tokens: list[str], idf: dict[str, float]) -> Vector:
    counts = Counter(tokens)
    if not counts:
        return {}
    length = sum(counts.values())
    vector = {token: (count / length) * idf.get(token, 1.0) for token, count in counts.items()}
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm == 0:
        return vector
    return {token: value / norm for token, value in vector.items()}


def cosine(left: Vector, right: Vector) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def dense_cosine(left: DenseVector, right: DenseVector) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
