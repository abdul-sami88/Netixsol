"""
Grounded RAG (Retrieval-Augmented Generation) Engine
Retrieves authoritative course material from TutorVectorDB with exact video timestamp links
and adapts pedagogical explanations to learner mastery tiers.
"""

from typing import Dict, Any, List, Optional
import os
import json
from content_pipeline.vector_store import TutorVectorDB

class GroundedRAGRetriever:
    """
    Retrieves syllabus content, transcripts, slides, and notes.
    Constrains tutor knowledge strictly to verified course assets.
    """

    def __init__(self, db_path: str = "data/content_vector_db.json"):
        self.db_path = db_path
        self.vector_db = TutorVectorDB(db_path)

    def retrieve_grounding_context(
        self,
        query: str,
        top_k: int = 3,
        concept_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Searches knowledge base for relevant chunks, extracting timestamps and slide references.
        """
        filter_dict = {"concept_id": concept_filter} if concept_filter else None
        results = self.vector_db.search(query=query, top_k=top_k, filter_dict=filter_dict)

        grounding_passages = []
        video_timestamps = []
        slide_references = []

        for r in results:
            meta = r["metadata"]
            media = meta.get("media_type", "text")
            title = meta.get("lesson_title", "Python Core")
            ts = meta.get("timestamp_label", None)
            slide_no = meta.get("slide_number", None)

            grounding_passages.append(r["text"])

            if media == "video_transcript" and ts:
                video_timestamps.append({
                    "lesson_id": meta.get("lesson_id", ""),
                    "lesson_title": title,
                    "timestamp_range": ts,
                    "relevance_score": r["score"]
                })
            elif media == "slide" and slide_no:
                slide_references.append({
                    "lesson_title": title,
                    "slide_number": slide_no,
                    "relevance_score": r["score"]
                })

        return {
            "query": query,
            "passages": grounding_passages,
            "primary_context": "\n\n".join(grounding_passages[:2]) if grounding_passages else "",
            "video_timestamps": video_timestamps,
            "slide_references": slide_references
        }

    @staticmethod
    def format_citation_link(video_timestamps: List[Dict[str, Any]], language: str = "english") -> str:
        """
        Generates user-facing video jump link citation.
        """
        if not video_timestamps:
            return ""
        top_ts = video_timestamps[0]
        title = top_ts["lesson_title"]
        ts = top_ts["timestamp_range"]

        if language.lower() == "urdulish":
            return f"\n\n📺 *Course Video Reference:* {title} par exact clip dekhein `{ts}`."
        return f"\n\n📺 *Course Video Reference:* Rewatch {title} at timestamp `{ts}` for the instructor's breakdown."
