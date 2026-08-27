"""
retriever.py — Task 2 step 5 + Task 3 (structured vs. semantic split).

WHY THE SPLIT (see README for the full justification):
- Prices, availability, plot sizes (area), bedrooms/baths, and agent/agency
  names are exact, structured, frequently-updated fields that live natively
  as typed columns in `properties`. Answering "how much" / "how many" /
  "who is the agent" from a vector store risks the embedding model
  retrieving a *similar-sounding* but wrong property (hallucination risk),
  and vector search cannot do exact filtering/aggregation ("under 8M",
  "3 bedrooms", "MAX/MIN/AVG price in DHA"). SQL against typed columns is
  exact, cheap, and trivially auditable — a hallucination is structurally
  impossible if the answer is echoed straight from a query result.
- Brochure text, descriptions, and FAQs are free-form natural language
  with no fixed schema — the only way to search them by meaning is
  semantic (embedding) similarity.

`HybridRetriever.retrieve()` classifies the query (keyword/regex based
router) and dispatches to SQL, vector search, or both, then returns a
single `RetrievalResult` the generator can ground an answer in.
"""
from __future__ import annotations
import re
import sqlite3
from dataclasses import dataclass, field


@dataclass
class RetrievalResult:
    structured_rows: list[dict] = field(default_factory=list)
    semantic_chunks: list[tuple] = field(default_factory=list)  # (Chunk, score)
    sql_used: str | None = None
    route: str = ""


STRUCTURED_KEYWORDS = [
    "price", "cost", "how much", "expensive", "cheap", "budget",
    "available", "availability", "for sale", "for rent", "rent for", "rental",
    "plot size", "area", "marla", "kanal", "sqft", "square feet",
    "agent", "agency", "who is selling", "who listed",
    "bedroom", "bedrooms", "bath", "baths", "cheapest", "most expensive",
    "average price", "how many properties",
]
SEMANTIC_KEYWORDS = [
    "amenit", "brochure", "describe", "description", "what is it like",
    "faq", "how does", "document", "tax", "installment",
    "power of attorney", "kanal", "included", "feature", "overseas",
]


SPECULATIVE_PATTERNS = [
    "will ", "predict", "forecast", "double in", "go up", "go down",
    "increase in the next", "decrease in the next", "future price",
    "interest rate", "policy rate", "state bank",
]


def classify_query(q: str) -> str:
    """Returns one of: structured, semantic, hybrid, none.
    IMPORTANT: if NEITHER a structured nor a semantic domain keyword is
    present, we do NOT default to "hybrid" and search anyway - that was
    the original design and it silently grounded out-of-domain questions
    (interest rates, price-prediction speculation) in irrelevant retrieved
    rows/chunks, producing a confident-looking but hallucinated answer.
    Returning "none" here makes the pipeline refuse instead, which is the
    correct behavior for genuinely out-of-scope questions."""
    ql = q.lower()
    if any(p in ql for p in SPECULATIVE_PATTERNS):
        # No amount of retrieval grounds a prediction/forecast - our data
        # is historical listings, not a forecasting model. Refuse rather
        # than answer from superficially-matched keywords like "price".
        return "none"
    struct_hit = any(k in ql for k in STRUCTURED_KEYWORDS)
    sem_hit = any(k in ql for k in SEMANTIC_KEYWORDS)
    if struct_hit and sem_hit:
        return "hybrid"
    if struct_hit:
        return "structured"
    if sem_hit:
        return "semantic"
    return "none"


class StructuredRetriever:
    """SQL-only retrieval over properties/locations/payment_plans/etc."""
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # --- convenience builders used by the query-understanding layer ---
    def filter_properties(self, city=None, max_price=None, min_price=None,
                           bedrooms=None, purpose=None, property_type=None,
                           locality=None, limit=20) -> list[dict]:
        clauses, params = [], []
        if city:
            clauses.append("city = ?"); params.append(city)
        if locality:
            clauses.append("locality LIKE ?"); params.append(f"%{locality}%")
        if max_price:
            clauses.append("price <= ?"); params.append(max_price)
        if min_price:
            clauses.append("price >= ?"); params.append(min_price)
        if bedrooms:
            clauses.append("bedrooms = ?"); params.append(bedrooms)
        if purpose:
            clauses.append("purpose = ?"); params.append(purpose)
        if property_type:
            clauses.append("property_type = ?"); params.append(property_type)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM properties {where} ORDER BY price ASC LIMIT ?"
        params.append(limit)
        return self.query(sql, tuple(params))

    def agent_for_property(self, property_id: int) -> dict | None:
        rows = self.query("SELECT agent, agency FROM properties WHERE property_id=?", (property_id,))
        return rows[0] if rows else None

    def price_stats(self, city=None, purpose="For Sale") -> dict:
        where = "WHERE purpose=?"
        params = [purpose]
        if city:
            where += " AND city=?"
            params.append(city)
        sql = f"SELECT MIN(price) min_price, MAX(price) max_price, AVG(price) avg_price, COUNT(*) n FROM properties {where}"
        return self.query(sql, tuple(params))[0]


class SemanticRetriever:
    """Vector-only retrieval over the description/FAQ corpus."""
    def __init__(self, vector_store):
        self.store = vector_store

    def search(self, query: str, top_k: int = 5):
        return self.store.search(query, top_k=top_k)


class HybridRetriever:
    def __init__(self, structured: StructuredRetriever, semantic: SemanticRetriever):
        self.structured = structured
        self.semantic = semantic

    def retrieve(self, query: str, filters: dict | None = None, top_k: int = 5) -> RetrievalResult:
        route = classify_query(query)
        result = RetrievalResult(route=route)
        filters = filters or {}

        if route in ("structured", "hybrid"):
            ql = query.lower()
            filters = dict(filters)  # don't mutate caller's dict
            pid = filters.pop("property_id", None)

            if pid is not None:
                rows = self.structured.query("SELECT * FROM properties WHERE property_id=?", (pid,))
            elif "average" in ql or "avg" in ql:
                purpose = filters.get("purpose", "For Sale")
                rows = [self.structured.price_stats(city=filters.get("city"), purpose=purpose)]
            elif "cheapest" in ql or "lowest price" in ql:
                rows = self.structured.filter_properties(limit=1, **filters) if filters else \
                       self.structured.query("SELECT * FROM properties ORDER BY price ASC LIMIT 1")
            elif "most expensive" in ql:
                base = self.structured.filter_properties(limit=1000, **filters) if filters else \
                       self.structured.query("SELECT * FROM properties ORDER BY price DESC LIMIT 1")
                rows = sorted(base, key=lambda r: r["price"], reverse=True)[:1] if filters else base
            elif filters:
                rows = self.structured.filter_properties(limit=top_k, **filters)
            else:
                rows = []
            result.structured_rows = rows

        if route in ("semantic", "hybrid"):
            result.semantic_chunks = self.semantic.search(query, top_k=top_k)

        return result
