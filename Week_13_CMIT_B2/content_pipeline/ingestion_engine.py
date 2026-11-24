"""
Content Ingestion Engine
Orchestrates Whisper video transcription indexing, slide decks, instructor notes,
and builds the indexed vector database.
"""

import os
import json
from typing import Dict, Any, List
from content_pipeline.sample_content import SAMPLE_LESSONS
from content_pipeline.whisper_transcriber import WhisperTranscriber
from content_pipeline.slide_notes_extractor import SlideNotesExtractor
from content_pipeline.vector_store import TutorVectorDB

class ContentIngestionEngine:
    """
    Complete ingestion pipeline converting multi-modal course materials into
    a searchable, timestamped knowledge vector store.
    """

    def __init__(self, db_storage_path: str = "data/content_vector_db.json"):
        self.db_storage_path = db_storage_path
        self.transcriber = WhisperTranscriber()
        self.extractor = SlideNotesExtractor()
        self.vector_db = TutorVectorDB()

    def run_ingestion(self, lessons_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes full ingestion pipeline over lesson transcripts, slides, and notes.
        """
        if lessons_data is None:
            lessons_data = SAMPLE_LESSONS

        all_docs = []
        all_metas = []
        all_ids = []

        total_segments = 0
        total_slides = 0
        total_notes = 0

        for lesson in lessons_data:
            l_id = lesson["lesson_id"]
            title = lesson["title"]

            # 1. Process Whisper Transcript Segments
            whisper_chunks = self.transcriber.process_transcript_segments(
                lesson_id=l_id,
                lesson_title=title,
                raw_segments=lesson.get("transcripts", []),
                chunk_target_seconds=60.0
            )
            for chunk in whisper_chunks:
                all_docs.append(chunk["text"])
                all_metas.append(chunk)
                all_ids.append(chunk["chunk_id"])
                total_segments += 1

            # 2. Process Slides
            slide_chunks = self.extractor.process_slides(
                lesson_id=l_id,
                lesson_title=title,
                slides_data=lesson.get("slides", [])
            )
            for chunk in slide_chunks:
                all_docs.append(chunk["text"])
                all_metas.append(chunk)
                all_ids.append(chunk["chunk_id"])
                total_slides += 1

            # 3. Process Notes
            notes_chunks = self.extractor.process_notes(
                lesson_id=l_id,
                lesson_title=title,
                notes_data=lesson.get("notes", [])
            )
            for chunk in notes_chunks:
                all_docs.append(chunk["text"])
                all_metas.append(chunk)
                all_ids.append(chunk["chunk_id"])
                total_notes += 1

        # Populate Vector DB
        self.vector_db.add_documents(all_docs, all_metas, all_ids)
        self.vector_db.build_index()
        self.vector_db.save(self.db_storage_path)

        summary = {
            "total_lessons_ingested": len(lessons_data),
            "whisper_transcript_chunks": total_segments,
            "slide_cards_indexed": total_slides,
            "instructor_notes_indexed": total_notes,
            "total_documents_indexed": len(all_docs),
            "db_path": self.db_storage_path
        }
        return summary

    def search_content(
        self,
        query: str,
        top_k: int = 3,
        media_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Queries the knowledge base and returns matching chunks with timestamp jumps.
        """
        filter_dict = {"media_type": media_filter} if media_filter else None
        return self.vector_db.search(query=query, top_k=top_k, filter_dict=filter_dict)


if __name__ == "__main__":
    engine = ContentIngestionEngine()
    stats = engine.run_ingestion()
    print("Ingestion Complete:")
    print(json.dumps(stats, indent=2))

    # Test Search
    test_queries = [
        "Why does range() stop early?",
        "Difference between print and return",
        "Mutable default arguments in functions",
        "How do dictionary lookups achieve O(1)?"
    ]

    print("\n--- Testing Vector DB Search & Timestamps ---")
    for q in test_queries:
        print(f"\nQuery: '{q}'")
        results = engine.search_content(q, top_k=2)
        for r in results:
            meta = r["metadata"]
            ts = meta.get("timestamp_label", "N/A")
            media = meta.get("media_type")
            title = meta.get("lesson_title")
            print(f"  [{media.upper()}] {title} | Timestamp: {ts} | Score: {r['score']}")
            print(f"  Snippet: {r['text'][:120]}...")

