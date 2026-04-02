"""
jarvis_memory_semantic.py — Semantic search + keyword extraction for JARVIS memory.

sentence-transformers is optional:
  pip install sentence-transformers

When not installed, falls back to TF-IDF-style keyword vectors for approximate
semantic similarity (less accurate but functional).
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger("jarvis.memory.semantic")

# ── Sentence Transformers (optional) ──────────────────────────────────────────

_ST_AVAILABLE = False
_st_model = None
_ST_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def _load_st_model():
    """Lazy-load sentence-transformers model. Returns model or None."""
    global _st_model, _ST_AVAILABLE
    if _st_model is not None:
        return _st_model
    try:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer(_ST_MODEL_NAME)
        _ST_AVAILABLE = True
        logger.info("[SEMANTIC] sentence-transformers model loaded: %s", _ST_MODEL_NAME)
        return _st_model
    except ImportError:
        logger.warning("[SEMANTIC] sentence-transformers not installed — fallback to keyword vectors")
        return None
    except Exception as e:
        logger.warning("[SEMANTIC] Could not load ST model: %s — using fallback", e)
        return None


# ── Italian stop words ────────────────────────────────────────────────────────

_IT_STOPWORDS = {
    "il","lo","la","i","gli","le","un","uno","una","e","è","di","da","in",
    "con","su","per","tra","fra","a","ad","al","allo","alla","ai","agli","alle",
    "del","dello","della","dei","degli","delle","nel","nello","nella","nei",
    "negli","nelle","sul","sullo","sulla","sui","sugli","sulle","che","chi",
    "cui","non","si","ne","ci","vi","mi","ti","lo","la","li","le","gli","ce",
    "ma","o","od","se","però","perché","come","quando","mentre","dove","cosa",
    "questo","questa","questi","queste","quello","quella","quelli","quelle",
    "ho","hai","ha","abbiamo","avete","hanno","sono","sei","siamo","siete",
    "mi","ti","ci","vi","mi","mio","tuo","suo","nostro","vostro","loro",
    "molto","troppo","poco","più","meno","già","ancora","sempre","mai",
    "oggi","ieri","domani","ora","adesso","poi","dopo","prima","anche",
    "solo","proprio","tutto","tutti","tutta","tutte","ogni","nessuno",
    "ho","hai","ha","avevo","aveva","avrei","avrebbe","stare","essere","fare",
    "vuoi","voglio","posso","puoi","devo","puoi","sai","so","va","vado",
    "qui","là","qua","lì", "the","a","is","are","was","were","of","in",
}

_KEYWORD_CATEGORIES = {
    "stress":      ["stress","stressato","ansia","anxious","tensione","preoccup","nervos","agitat"],
    "lavoro":      ["lavoro","studio","progetto","deadline","scadenza","esame","coding","git"],
    "benessere":   ["pausa","break","passeggiata","riposo","sonno","dormito","rilassato","bene"],
    "emozioni_neg":["triste","depress","male","stanco","esausto","giù","basso","piango"],
    "emozioni_pos":["felice","contento","bene","bello","ottimo","fantastico","allegro","energia"],
    "cibo":        ["mangiato","pranzo","cena","colazione","caffè","fame","cibo"],
    "esercizio":   ["palestra","gym","corsa","sport","allenamento","camminato","mossa"],
}


def _vectorize_keywords(text: str) -> np.ndarray:
    """
    Fallback: convert text to a keyword-frequency vector (dim = len(_KEYWORD_CATEGORIES)).
    Normalized to unit vector for cosine similarity.
    """
    text_lower = text.lower()
    vec = np.zeros(len(_KEYWORD_CATEGORIES), dtype=np.float32)
    for i, (cat, kws) in enumerate(_KEYWORD_CATEGORIES.items()):
        count = sum(1 for kw in kws if kw in text_lower)
        vec[i] = count
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def _embed_text(text: str, model=None) -> np.ndarray:
    """Return embedding vector. Uses ST model if available, else keyword vector."""
    if model is not None:
        try:
            emb = model.encode(text, convert_to_numpy=True)
            norm = np.linalg.norm(emb)
            return (emb / norm).astype(np.float32) if norm > 0 else emb.astype(np.float32)
        except Exception as e:
            logger.warning("[SEMANTIC] Embedding failed: %s", e)
    return _vectorize_keywords(text)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two unit vectors."""
    if a.shape != b.shape or np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b))


def _vec_to_bytes(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def _bytes_to_vec(data: bytes, dim: int = 0) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.float32)
    return arr


class SemanticMemoryManager:
    """
    Adds semantic search and keyword enrichment to JarvisMemory.
    Runs fully locally — no cloud API for embeddings.
    """

    def __init__(self, memory=None):
        if memory is None:
            from jarvis_memory import JarvisMemory
            memory = JarvisMemory()
        self.memory = memory
        self._model = None  # loaded lazily

    def _get_model(self):
        if self._model is None:
            self._model = _load_st_model()
        return self._model

    # ── Embedding management ──────────────────────────────────────────────────

    def add_embedding(self, conversation_id: int, text: str) -> bool:
        """Generate and store embedding for a conversation."""
        try:
            model = self._get_model()
            vec = _embed_text(text, model)
            self.memory.save_embedding(conversation_id, _vec_to_bytes(vec))
            return True
        except Exception as e:
            logger.warning("[SEMANTIC] Could not add embedding: %s", e)
            return False

    def add_conversation_with_embedding(
        self,
        user_input: str,
        response: str,
        mood: str = "neutral",
        intent: str = "unknown",
        context: Optional[dict] = None,
    ) -> int:
        """
        Save conversation + extract keywords + store embedding.
        Returns conversation_id.
        """
        keywords = self.extract_keywords(f"{user_input} {response}")
        ctx = dict(context or {})
        ctx["keywords"] = keywords

        self.memory.save_conversation(
            user_input=user_input,
            jarvis_response=response,
            mood_detected=mood,
            intent=intent,
            context=ctx,
        )
        # Get the ID of the row we just inserted
        convs = self.memory.get_recent_conversations(limit=1)
        if convs:
            conv_id = convs[-1]["id"]
            combined = f"{user_input} {response}"
            self.add_embedding(conv_id, combined)
            # Also save mood timeline entry
            self.memory.save_mood_timeline(
                mood_label=mood,
                mood_score=self._mood_to_score(mood),
                keywords=keywords,
            )
            return conv_id
        return -1

    # ── Semantic search ───────────────────────────────────────────────────────

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Find top-k most semantically similar past conversations.

        Returns list of dicts:
        {conversation_id, user_input, jarvis_response, mood, timestamp, similarity}
        """
        model = self._get_model()
        query_vec = _embed_text(query, model)

        # Load all stored embeddings
        rows = self.memory.get_embeddings()
        if not rows:
            return []

        scored: list[tuple[float, dict]] = []
        for row in rows:
            try:
                stored_vec = _bytes_to_vec(row["embedding"])
                sim = _cosine_similarity(query_vec, stored_vec)
                if sim > 0:
                    scored.append((sim, row))
            except Exception:
                continue

        # Sort descending, return top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, row in scored[:top_k]:
            conv = self.memory.get_conversation_by_id(row["conversation_id"])
            if conv:
                results.append({
                    "conversation_id": row["conversation_id"],
                    "user_input":      conv.get("user_input", ""),
                    "jarvis_response": conv.get("jarvis_response", ""),
                    "mood":            conv.get("mood_detected", ""),
                    "timestamp":       conv.get("timestamp", ""),
                    "similarity":      round(sim, 4),
                })
        return results

    # ── Keyword extraction ────────────────────────────────────────────────────

    def extract_keywords(self, text: str, max_keywords: int = 8) -> list[str]:
        """
        Extract relevant Italian/English keywords from text.
        Returns list of lowercase keyword strings.
        """
        # Tokenize
        tokens = re.findall(r"\b[a-zA-ZÀ-ÿ]{3,}\b", text.lower())
        # Remove stopwords
        tokens = [t for t in tokens if t not in _IT_STOPWORDS]

        # Frequency count
        freq: dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1

        # Also check category keywords
        category_hits = []
        text_lower = text.lower()
        for cat, kws in _KEYWORD_CATEGORIES.items():
            if any(kw in text_lower for kw in kws):
                category_hits.append(cat)

        # Combine: top freq tokens + category labels
        top_tokens = sorted(freq, key=freq.get, reverse=True)[:max_keywords]
        combined = list(dict.fromkeys(top_tokens + category_hits))  # preserve order, dedup
        return combined[:max_keywords]

    # ── Similar mood finder ───────────────────────────────────────────────────

    def find_similar_moods(
        self, current_mood: str, lookback_days: int = 7
    ) -> list[dict]:
        """
        Find past conversations where the mood matched current_mood.
        Returns list with timestamp, conversation excerpt, and what helped.
        """
        cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()
        rows = self.memory.get_recent_conversations(limit=50)

        matches = []
        for conv in rows:
            if conv.get("mood_detected") != current_mood:
                continue
            ts = conv.get("timestamp", "")
            if ts and ts < cutoff:
                continue
            response = conv.get("jarvis_response", "")
            keywords = conv.get("context", {}).get("keywords", [])
            matches.append({
                "timestamp":       ts,
                "user_input":      conv.get("user_input", "")[:80],
                "jarvis_response": response[:120],
                "keywords":        keywords[:5],
                "mood":            current_mood,
            })

        return matches[:5]

    # ── Mood timeline enrichment ──────────────────────────────────────────────

    def get_mood_trend(self, days: int = 7) -> dict:
        """
        Compute mood trend over recent N days.
        Returns: {trend, avg_score, direction, description}
        """
        timeline = self.memory.get_mood_timeline(days=days)
        if not timeline:
            return {
                "trend": "unknown", "avg_score": 5.0,
                "direction": "stable", "description": "Nessun dato disponibile.",
            }

        scores = [row["mood_score"] for row in timeline if row.get("mood_score") is not None]
        if not scores:
            return {"trend": "unknown", "avg_score": 5.0, "direction": "stable",
                    "description": "Nessun dato disponibile."}

        avg = sum(scores) / len(scores)

        # Compute linear trend (first half vs second half)
        mid = len(scores) // 2
        if mid > 0:
            first_avg = sum(scores[:mid]) / mid
            second_avg = sum(scores[mid:]) / len(scores[mid:])
            delta = second_avg - first_avg
        else:
            delta = 0.0

        if delta > 0.5:
            direction = "improving"
            emoji = "📈"
        elif delta < -0.5:
            direction = "declining"
            emoji = "📉"
        else:
            direction = "stable"
            emoji = "📊"

        description = f"Umore medio {days}gg: {avg:.1f}/10 {emoji} ({direction})"

        return {
            "trend":       direction,
            "avg_score":   round(avg, 2),
            "direction":   direction,
            "description": description,
            "emoji":       emoji,
            "n_points":    len(scores),
        }

    # ── Context builder ───────────────────────────────────────────────────────

    def build_enhanced_context(
        self,
        query: str,
        mood: str,
        max_similar: int = 3,
    ) -> str:
        """
        Build enriched context string for Sonnet system prompt.
        Includes: mood trend + similar past situations + what helped.
        """
        parts = []

        # Mood trend
        trend = self.get_mood_trend(days=7)
        parts.append(f"Trend umore 7gg: {trend['description']}")

        # Similar past situations
        similar = self.semantic_search(query, top_k=max_similar)
        if similar:
            parts.append("Situazioni simili in passato:")
            for s in similar:
                ts = s["timestamp"][:10] if s.get("timestamp") else "?"
                parts.append(
                    f"  [{ts}] similarity={s['similarity']:.2f} "
                    f"mood={s['mood']}: \"{s['user_input'][:60]}...\""
                )

        # What helped when in similar mood
        similar_moods = self.find_similar_moods(mood, lookback_days=7)
        if similar_moods:
            parts.append(f"Quando eri '{mood}' di recente, JARVIS disse:")
            for sm in similar_moods[:2]:
                parts.append(f"  \"{sm['jarvis_response'][:80]}\"")

        return "\n".join(parts) if parts else ""

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _mood_to_score(mood: str) -> float:
        _SCORES = {
            "happy": 9.0, "excited": 8.5, "calm": 7.0, "neutral": 5.0,
            "tired": 4.0, "anxious": 3.5, "stressed": 3.0, "sad": 2.5,
            "angry": 2.0, "depressed": 1.5,
        }
        return _SCORES.get(mood.lower(), 5.0)
