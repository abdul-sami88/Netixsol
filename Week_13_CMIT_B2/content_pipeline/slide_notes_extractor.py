"""
Slide and Notes Extractor Module
Extracts presentation slides and instructor pedagogical notes into structured learning objects.
"""

from typing import List, Dict, Any

class SlideNotesExtractor:
    """
    Extracts, cleans, and chunks slides and instructor notes for vector indexing.
    """

    def process_slides(
        self,
        lesson_id: str,
        lesson_title: str,
        slides_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Processes slide deck data into indexable chunks.
        """
        chunks = []
        for slide in slides_data:
            slide_no = slide.get("slide_number", 1)
            title = slide.get("title", "")
            content = slide.get("content", "")
            ts = slide.get("timestamp", "00:00")
            
            full_text = f"Slide {slide_no}: {title}\n{content}"
            chunks.append({
                "chunk_id": f"{lesson_id}_slide_{slide_no:02d}",
                "lesson_id": lesson_id,
                "lesson_title": lesson_title,
                "media_type": "slide",
                "slide_number": slide_no,
                "timestamp_label": ts,
                "title": title,
                "text": full_text
            })
        return chunks

    def process_notes(
        self,
        lesson_id: str,
        lesson_title: str,
        notes_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Processes instructor lecture notes and misconception guides into indexable chunks.
        """
        chunks = []
        for idx, note in enumerate(notes_data):
            section = note.get("section", "Lecture Note")
            content = note.get("content", "")
            
            full_text = f"{lesson_title} - {section}:\n{content}"
            chunks.append({
                "chunk_id": f"{lesson_id}_notes_{idx:02d}",
                "lesson_id": lesson_id,
                "lesson_title": lesson_title,
                "media_type": "instructor_notes",
                "section": section,
                "text": full_text
            })
        return chunks

