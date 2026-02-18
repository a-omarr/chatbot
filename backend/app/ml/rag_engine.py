"""RAG (Retrieval-Augmented Generation) engine for the Toros Yazılım chatbot.

Uses cross-lingual TF-IDF with character n-grams for semantic-like search.
100% free — no API key, no large model download. Only scikit-learn + numpy.

The pipeline:
1. Index all knowledge base entries across ALL languages on startup
2. When a query comes in, vectorise it and find the most similar KB entries
3. Boost entries in the user's target language
4. Return the best-matching answer from the knowledge base

Character n-grams (3-6) work across scripts (Latin, Cyrillic, Arabic)
so that e.g. "toros" matches Turkish, English, Arabic, and Russian entries.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cross-Lingual TF-IDF Knowledge Index
# ---------------------------------------------------------------------------


class KnowledgeIndex:
    """Embeds and indexes all knowledge base entries for fast cross-lingual search.

    Uses character n-gram TF-IDF so that it naturally handles multiple
    scripts (Latin, Cyrillic, Arabic) without language-specific tokenisers.
    """

    def __init__(self, knowledge_base: dict[str, list[dict[str, Any]]]):
        self._kb = knowledge_base
        self._entries: list[dict[str, Any]] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._built = False

    def build(self) -> None:
        """Build the TF-IDF index from the knowledge base."""
        self._entries = []
        texts_to_embed: list[str] = []

        for lang, items in self._kb.items():
            for item in items:
                entry = {
                    "lang": lang,
                    "title": item.get("title", ""),
                    "keywords": item.get("keywords", []),
                    "answer": item.get("answer", ""),
                }
                self._entries.append(entry)
                # Combine title + keywords + answer for richer indexing
                embed_text = (
                    f"{entry['title']} "
                    f"{' '.join(entry['keywords'])} "
                    f"{entry['answer'][:500]}"
                )
                texts_to_embed.append(embed_text)

        if texts_to_embed:
            # Character n-grams work across all scripts (Latin, Cyrillic, Arabic)
            self._vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 6),
                min_df=1,
                max_df=0.95,
                sublinear_tf=True,
            )
            self._tfidf_matrix = self._vectorizer.fit_transform(texts_to_embed)

        self._built = True
        logger.info(f"Knowledge index built with {len(self._entries)} entries.")

    def retrieve(
        self, query: str, lang: str = "en", top_k: int = 3
    ) -> list[dict[str, Any]]:
        """Find the top-k most similar KB entries across all languages.

        Matches in the user's selected language receive a 1.3× score boost.
        """
        if not self._built:
            self.build()

        if self._vectorizer is None or self._tfidf_matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        # Strongly prefer entries in the user's language
        for i, entry in enumerate(self._entries):
            if entry["lang"] == lang:
                scores[i] *= 2.0
            else:
                scores[i] *= 0.5

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            entry = self._entries[idx].copy()
            entry["score"] = float(scores[idx])
            results.append(entry)

        return results


# ---------------------------------------------------------------------------
# Global index (lazy-built on first query)
# ---------------------------------------------------------------------------
_index: KnowledgeIndex | None = None


async def generate_answer(
    query: str,
    knowledge_base: dict[str, list[dict[str, Any]]],
    lang: str = "en",
) -> str | None:
    """Find the best answer using cross-lingual TF-IDF search over the KB.

    Returns the answer text of the best-matching KB entry, or None if
    no entry scores above the similarity threshold.
    """
    global _index

    if _index is None:
        _index = KnowledgeIndex(knowledge_base)
        _index.build()

    results = _index.retrieve(query, lang=lang, top_k=1)

    if not results:
        return None

    best = results[0]
    # Only return an answer if similarity is high enough
    if best["score"] < 0.08:
        return None

    return best["answer"]
