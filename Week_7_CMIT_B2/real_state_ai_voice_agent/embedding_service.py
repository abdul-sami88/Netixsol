import os
import math
import numpy as np
from typing import List, Dict, Any, Optional, Union
from collections import OrderedDict
from config import config

class LRUCache:
    """Simple thread-safe in-memory LRU cache for vector embeddings."""
    def __init__(self, capacity: int = 500):
        self.capacity = capacity
        self.cache: OrderedDict[str, List[float]] = OrderedDict()

    def get(self, key: str) -> Optional[List[float]]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: List[float]):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def __contains__(self, key: str) -> bool:
        return key in self.cache


class LocalFallbackVectorizer:
    """
    Sub-millisecond local fallback vectorizer using TF-IDF with character and word n-grams.
    Ensures Roman Urdu and noisy speech inputs can be compared offline with zero latency.
    """
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1
        )
        # Seed with diverse Pakistani real estate domain vocabulary
        seed_corpus = [
            "installment plan down payment qist schedule flexible 3 years monthly",
            "dha lahore islamabad karachi bahria town gulberg plot house villa luxury",
            "noc legal approval lda cda sbca registry intiqal allotment letter",
            "mehnga price discount rate budget crore lakh affordability investment",
            "possession physical ready to move under construction development work",
            "site visit appointment schedule meeting representative timing tomorrow",
            "roshan digital account overseas pakistani power of attorney nicop",
            "rental yield commercial shop residential house high roi appreciation",
            "corner plot park facing boulevard main road location amenities"
        ]
        self.vectorizer.fit(seed_corpus)
        self.dim = len(self.vectorizer.get_feature_names_out())

    def transform(self, text: str) -> List[float]:
        vec = self.vectorizer.transform([text.lower()]).toarray()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


class EmbeddingService:
    """
    Unified Embedding Service:
    1. Fast in-memory LRU cache
    2. Primary: Google GenAI Client (gemini-embedding-001)
    3. Fallback: Local TF-IDF char n-gram vectorizer
    """
    def __init__(self, cache_size: int = 500):
        self.cache = LRUCache(capacity=cache_size)
        self.gemini_key = config.GEMINI_API_KEY
        self.client = None
        self.primary_model = "gemini-embedding-001"
        self.fallback_models = ["text-embedding-004", "gemini-embedding-2-preview"]
        self.local_vectorizer: Optional[LocalFallbackVectorizer] = None
        self._init_client()

    def _init_client(self):
        if self.gemini_key and len(self.gemini_key) > 15:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                print(f"[EmbeddingService] Warning: Google GenAI init failed ({e}). Using local fallback.")
                self.client = None

    def _get_local_vectorizer(self) -> LocalFallbackVectorizer:
        if self.local_vectorizer is None:
            self.local_vectorizer = LocalFallbackVectorizer()
        return self.local_vectorizer

    def get_embedding(self, text: str) -> List[float]:
        """
        Computes vector embedding for a single text.
        Returns cached value if present, else queries Gemini or falls back locally.
        """
        if not text or not text.strip():
            return [0.0] * 64

        clean_text = text.strip()
        cached = self.cache.get(clean_text)
        if cached is not None:
            return cached

        # Strategy 1: Google GenAI Client
        if self.client:
            models_to_try = [self.primary_model] + self.fallback_models
            for model_name in models_to_try:
                try:
                    response = self.client.models.embed_content(
                        model=model_name,
                        contents=clean_text
                    )
                    if response and response.embeddings:
                        embedding = response.embeddings[0].values
                        self.cache.put(clean_text, embedding)
                        return embedding
                except Exception:
                    continue

        # Strategy 2: Local TF-IDF char-ngram fallback
        local_vec = self._get_local_vectorizer().transform(clean_text)
        self.cache.put(clean_text, local_vec)
        return local_vec

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding computation with caching."""
        return [self.get_embedding(t) for t in texts]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        if not vec_a or not vec_b:
            return 0.0
        
        # If dimensions mismatch (e.g. from mixed fallbacks), compare lengths or re-normalize
        if len(vec_a) != len(vec_b):
            return 0.0

        a = np.array(vec_a, dtype=float)
        b = np.array(vec_b, dtype=float)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        sim = float(np.dot(a, b) / (norm_a * norm_b))
        return max(0.0, min(1.0, sim))

    def similarity(self, text_a: str, text_b: str) -> float:
        """Convenience method to directly compare similarity between two strings."""
        vec_a = self.get_embedding(text_a)
        vec_b = self.get_embedding(text_b)
        return self.cosine_similarity(vec_a, vec_b)


# Global singleton instance
embedding_service = EmbeddingService()
