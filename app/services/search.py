"""Similarity search service using TF-IDF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class SearchCandidate:
    """Represents a ranked document candidate."""

    document_id: int
    filename: str
    title: str
    summary: str
    score: float
    explanation: str


def rank_documents(query: str, documents: Iterable[dict[str, str]]) -> list[SearchCandidate]:
    """Return the top two matching documents for the query."""
    doc_list = list(documents)
    if not doc_list:
        return []

    analyzer = TfidfVectorizer(stop_words="english")
    doc_texts = [doc["content"] for doc in doc_list]
    doc_matrix = analyzer.fit_transform(doc_texts)
    query_vector = analyzer.transform([query])
    scores = cosine_similarity(query_vector, doc_matrix).flatten()

    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for index in ranked_indices[:2]:
        doc = doc_list[index]
        results.append(
            SearchCandidate(
                document_id=doc["id"],
                filename=doc["filename"],
                title=doc["title"],
                summary=doc["summary"],
                score=float(scores[index]),
                explanation=_build_explanation(query, doc["content"]),
            )
        )
    return results


def _build_explanation(query: str, content: str) -> str:
    """Provide a brief explanation based on overlapping keywords."""
    vectorizer = TfidfVectorizer(stop_words="english")
    analyzer = vectorizer.build_analyzer()
    query_terms = set(analyzer(query))
    doc_terms = set(analyzer(content))
    overlap = sorted(query_terms & doc_terms)
    if overlap:
        snippet = ", ".join(overlap[:5])
        return f"Overlapping terms: {snippet}."
    return "Similarity based on overall language overlap."
