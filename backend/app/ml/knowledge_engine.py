from __future__ import annotations

"""Knowledge retrieval engine for the Toros Yazılım chatbot.

Uses cross-lingual TF-IDF search to find the best matching answer in the
knowledge base. Supports Latin, Cyrillic, and Arabic scripts.
"""

import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class KnowledgeIndex:
    """Indexes knowledge base entries for fast semantic search via TF-IDF."""

    def __init__(self, knowledge_base: dict[str, list[dict[str, Any]]]):
        """Initialize with a dictionary of localized knowledge base entries."""
        self._kb = knowledge_base
        self._entries: list[dict[str, Any]] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._built = False

    def build(self) -> None:
        """Construct the TF-IDF search index from all KB entries."""
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
                
                # Create searchable text representation
                # Repeating title and keywords gives them higher weight in search
                embed_text = (
                    f"{entry['title']} {entry['title']} "
                    f"{' '.join(entry['keywords'])} {' '.join(entry['keywords'])} "
                    f"{entry['answer'][:500]}"
                )
                texts_to_embed.append(embed_text)

        if texts_to_embed:
            # Character n-grams (3-6) handle multilingual variability well
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
        """Retrieve the most relevant entries for a given query."""
        if not self._built:
            self.build()

        if self._vectorizer is None or self._tfidf_matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        # Weight entries in the user's preferred language more heavily
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

# Singleton index instance (lazy-built)
_index: KnowledgeIndex | None = None

async def generate_answer(
    query: str,
    knowledge_base: dict[str, list[dict[str, Any]]],
    lang: str = "en",
) -> str | None:
    """High-level function to retrieve a single best answer string."""
    global _index

    if _index is None:
        _index = KnowledgeIndex(knowledge_base)
        _index.build()

    results = _index.retrieve(query, lang=lang, top_k=1)

    if not results:
        return None

    best = results[0]
    # Similarity threshold to filter out noise
    if best["score"] < 0.08:
        return None

    return best["answer"]
