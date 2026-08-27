"""
embeddings.py — Task 2 step 3.

Two interchangeable embedding backends behind one interface:

1. GeminiEmbedder   — calls Google's `text-embedding-004` model via the
                       `google-generativeai` SDK. Used when GEMINI_API_KEY
                       is set. This sandbox has no outbound access to
                       Google's API domain, so it is provided as
                       production-ready code but is not exercised in the
                       demo run below.
2. TfidfEmbedder    — a fully local, deterministic fallback (scikit-learn
                       TF-IDF + SVD to a dense vector) so the pipeline is
                       runnable/testable offline and the retrieval logic,
                       chunk-size experiment, and eval harness all still work.

Swap backends with one line: `get_embedder(backend="gemini")` vs `"tfidf"`.
"""
from __future__ import annotations
import os
import numpy as np


class BaseEmbedder:
    def fit(self, texts: list[str]):
        raise NotImplementedError

    def embed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


class GeminiEmbedder(BaseEmbedder):
    """Wraps Gemini's embedding endpoint. Requires GEMINI_API_KEY.
    pip install google-generativeai
    """
    def __init__(self, model: str = "models/text-embedding-004"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai
        self.model = model

    def fit(self, texts: list[str]):
        return self  # no fitting needed, API is stateless

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for t in texts:
            resp = self._genai.embed_content(model=self.model, content=t,
                                              task_type="retrieval_document")
            vectors.append(resp["embedding"])
        return np.array(vectors, dtype=np.float32)


class TfidfEmbedder(BaseEmbedder):
    """Offline fallback: TF-IDF -> L2-normalized dense vectors via TruncatedSVD.
    No network calls, deterministic, good enough to demonstrate and evaluate
    the retrieval architecture end-to-end.
    """
    def __init__(self, n_components: int = 128):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self.n_components = n_components
        self.svd = None

    def fit(self, texts: list[str]):
        from sklearn.decomposition import TruncatedSVD
        X = self.vectorizer.fit_transform(texts)
        k = min(self.n_components, X.shape[1] - 1, X.shape[0] - 1)
        k = max(k, 2)
        self.svd = TruncatedSVD(n_components=k, random_state=42)
        self.svd.fit(X)
        return self

    def embed(self, texts: list[str]) -> np.ndarray:
        X = self.vectorizer.transform(texts)
        V = self.svd.transform(X)
        norms = np.linalg.norm(V, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return (V / norms).astype(np.float32)


def get_embedder(backend: str = "auto") -> BaseEmbedder:
    if backend == "gemini" or (backend == "auto" and os.environ.get("GEMINI_API_KEY")):
        try:
            return GeminiEmbedder()
        except Exception as e:
            print(f"[embeddings] Gemini backend unavailable ({e}); falling back to TF-IDF.")
    return TfidfEmbedder()
