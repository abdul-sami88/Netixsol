"""
generator.py — Task 2 step 6.

Answer generation is deliberately *extractive/templated*: the answer is
built only from fields actually present in `RetrievalResult`. This is the
core anti-hallucination guarantee — if nothing was retrieved, the agent
says so instead of guessing.

A `llm_generate()` hook is included for swapping in a real LLM (Claude/
Gemini) to phrase the final sentence more naturally, but it is instructed
to use ONLY the provided context and forbidden from adding outside facts.
Not called in this offline demo (no LLM API reachable from this sandbox);
the templated generator below is what's actually executed and evaluated.
"""
from __future__ import annotations
from retriever import RetrievalResult

NO_EVIDENCE_MSG = (
    "I couldn't find this in our verified property data, so I can't answer "
    "that reliably. Could you rephrase, or ask about a specific city, "
    "budget, or property?"
)


def format_property_row(r: dict) -> str:
    return (f"Property #{r.get('property_id')}: {r.get('bedrooms')}-bed {r.get('property_type')} "
            f"in {r.get('locality')}, {r.get('city')} — PKR {r.get('price'):,.0f} "
            f"({r.get('purpose')}), {r.get('area')}, {r.get('baths')} bath(s), "
            f"listed by {r.get('agent')} ({r.get('agency')}).")


def generate_answer(query: str, result: RetrievalResult) -> dict:
    """Returns {answer, citations, grounded} — citations point at the exact
    rows/chunks used, so grounding can be automatically verified later."""
    citations = []
    parts = []

    if result.structured_rows:
        # aggregate stats shape vs. row list shape
        first = result.structured_rows[0]
        if set(first.keys()) == {"min_price", "max_price", "avg_price", "n"}:
            parts.append(
                f"Across {first['n']} matching listings, prices range from "
                f"PKR {first['min_price']:,.0f} to PKR {first['max_price']:,.0f}, "
                f"averaging PKR {first['avg_price']:,.0f}."
            )
            citations.append({"source": "sql:price_stats"})
        else:
            for r in result.structured_rows[:5]:
                parts.append(format_property_row(r))
                citations.append({"source": "sql:properties", "property_id": r.get("property_id")})

    if result.semantic_chunks:
        for chunk, score in result.semantic_chunks[:3]:
            if score > 0.05:  # relevance floor - avoid grounding on noise
                parts.append(chunk.text)
                citations.append({"source": "vector", "chunk_id": chunk.chunk_id, "score": round(score, 3)})

    if not parts:
        return {"answer": NO_EVIDENCE_MSG, "citations": [], "grounded": False}

    answer = " ".join(parts)
    return {"answer": answer, "citations": citations, "grounded": True}


def llm_generate(query: str, result: RetrievalResult, call_llm):
    """Optional: pass a callable `call_llm(prompt:str)->str` (e.g. wrapping
    the Anthropic or Gemini API) to have an LLM phrase the final answer.
    The prompt hard-constrains it to the retrieved context only."""
    context_lines = []
    for r in result.structured_rows:
        context_lines.append(str(r))
    for chunk, score in result.semantic_chunks:
        context_lines.append(chunk.text)
    context = "\n".join(context_lines) if context_lines else "(no matching records found)"

    prompt = (
        "You are a real-estate assistant. Answer the user's question using "
        "ONLY the CONTEXT below. If the context does not contain the answer, "
        "say you don't have verified data for that — do not guess or use "
        "outside knowledge.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION: {query}\nANSWER:"
    )
    return call_llm(prompt)
