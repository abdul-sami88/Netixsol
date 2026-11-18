"""
query_router.py
Adaptive Query Router for Khan & Associates Legal Assistant.
Analyzes user legal query semantics, entity count, multi-hop relationship signals,
and routing rules to dynamically select:
1. VECTOR_RAG: Direct factual lookups, single-statute definitions, penalty provisions.
2. GRAPH_RAG: Relational traversals, overruled precedent checks, citation chains, bench composition.
3. HYBRID_RAG: Complex multi-hop legal analysis requiring both textual doctrine and relational validation.
"""

import re
from typing import Dict, Any, Tuple


class LegalQueryRouter:
    def __init__(self):
        # Lexical signals for Graph relationships
        self.graph_signals = [
            r"\boverruled\b",
            r"\boverrules\b",
            r"\bbad\s+law\b",
            r"\bprecedent\b",
            r"\bprecedents\b",
            r"\bcited\s+by\b",
            r"\bcites\b",
            r"\bcitation\b",
            r"\bcitations\b",
            r"\bbench\b",
            r"\bauthored\s+by\b",
            r"\bwhich\s+judgments\b",
            r"\bwhich\s+cases\b",
            r"\bwhich\s+supreme\s+court\s+judgments\b",
            r"\blist\s+judgments\b",
            r"\bfind\s+the\s+cases\b",
            r"\bpagerank\b",
            r"\bmost\s+authoritative\b",
            r"\bleading\s+cases\b",
            r"\bnetwork\b",
            r"\blater\s+overruled\b",
            r"\bsubsequent\s+bench\b",
            r"\bwho\s+were\s+the\s+bench\s+members\b",
            r"\bwhich\s+judges\b"
        ]
        
        # Lexical signals for Vector single-fact lookup
        self.vector_signals = [
            r"\bwhat\s+is\s+the\s+(?:statutory\s+)?definition\s+of\b",
            r"\bwhat\s+punishment\s+is\s+prescribed\b",
            r"\bwhat\s+does\s+article\s+\d+\s+state\b",
            r"\bwhat\s+are\s+the\s+powers\s+of\b",
            r"\bwhat\s+grounds\s+of\s+bail\b",
            r"\bwhat\s+is\s+the\s+requirement\s+of\b",
            r"\bwhat\s+agreements\s+are\s+contracts\b",
            r"\bwhat\s+constitutes\s+an\s+offence\b",
            r"\bwhat\s+are\s+the\s+rules\s+regarding\b",
            r"\bwhat\s+does\s+section\s+\d+\s+provide\b"
        ]
        
        # Lexical signals for Hybrid synthesis
        self.hybrid_signals = [
            r"\bcan\s+(?:an?\s+)?(?:agreement|contract)\s+(?:with|under).+?be\s+enforced\b",
            r"\bhow\s+do\s+pakistani\s+courts\s+treat\b",
            r"\bwhat\s+risk\s+does\s+it\s+pose\b",
            r"\bcan\s+an\s+aggrieved\s+party\s+seek\b",
            r"\bconsidering\s+section\s+\d+\s+and\s+recent\s+supreme\s+court\b",
            r"\bcommercial\s+contract\s+clause\s+references\b"
        ]

    def route(self, query: str) -> Dict[str, Any]:
        """
        Determines the optimal execution engine for a legal query.
        Returns engine choice, confidence, and reasoning.
        """
        q = query.lower().strip()
        
        # Check Hybrid signals first
        for sig in self.hybrid_signals:
            if re.search(sig, q):
                return {
                    "engine": "HYBRID_RAG",
                    "confidence": 0.95,
                    "reason": "Query requires doctrinal text extraction fused with precedent relational validation."
                }
                
        # Check Vector signals
        for sig in self.vector_signals:
            if re.search(sig, q):
                # Ensure no graph multi-hop terms override
                if not any(re.search(gs, q) for gs in [r"\boverruled\b", r"\bwhich\s+judgments\b", r"\bbad\s+law\b"]):
                    return {
                        "engine": "VECTOR_RAG",
                        "confidence": 0.92,
                        "reason": "Single-statute factual definition or penalty lookup; optimal for flat vector retrieval."
                    }
                    
        # Check Graph signals
        for sig in self.graph_signals:
            if re.search(sig, q):
                return {
                    "engine": "GRAPH_RAG",
                    "confidence": 0.96,
                    "reason": "Multi-hop relational query involving citation tracing, overruling status, or judicial bench composition."
                }
                
        # Default heuristic based on entity count and question words
        has_statute = bool(re.search(r"\b(?:section|article|act|order)\b", q))
        has_case = bool(re.search(r"\b(?:pld|scmr|clc|case|judgment)\b", q))
        
        if has_statute and has_case:
            return {
                "engine": "HYBRID_RAG",
                "confidence": 0.85,
                "reason": "Cross-domain query involving both statutory provision and case law precedent."
            }
        elif has_case:
            return {
                "engine": "GRAPH_RAG",
                "confidence": 0.88,
                "reason": "Case precedent inquiry; optimal for citation graph traversal."
            }
        else:
            return {
                "engine": "VECTOR_RAG",
                "confidence": 0.80,
                "reason": "Standard legal inquiry defaulting to vector retrieval."
            }


if __name__ == "__main__":
    router = LegalQueryRouter()
    sample_queries = [
        "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?",
        "What is the statutory definition of unlawful consideration under Section 23 of the Contract Act, 1872?",
        "Can an agreement with partially unlawful consideration be enforced in Pakistan, considering Section 23 and recent Supreme Court precedent?",
        "Has 1998 SCMR 1120 been overruled?",
        "What does Article 25 of the Constitution say about equality of citizens?"
    ]
    
    print("=" * 60)
    print("ADAPTIVE QUERY ROUTER DEMO")
    print("=" * 60)
    for sq in sample_queries:
        r = router.route(sq)
        print(f"\nQuery: {sq}")
        print(f"  -> Routed to: {r['engine']} (Confidence: {r['confidence']:.2f})")
        print(f"  -> Reason: {r['reason']}")

