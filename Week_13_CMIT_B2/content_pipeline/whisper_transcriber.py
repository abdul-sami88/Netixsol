"""
Whisper Transcriber Module
Handles video/audio transcription processing, timestamp alignment, and semantic segment chunking.
"""

from typing import List, Dict, Any, Optional
import json

class WhisperTranscriber:
    """
    Processes and standardizes Whisper transcription outputs with timestamp precision.
    Compatible with OpenAI Whisper JSON schema (segments with start, end, text).
    """

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Converts float seconds into mm:ss format."""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """Converts mm:ss or hh:mm:ss format to float seconds."""
        parts = list(map(float, timestamp_str.strip().split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return 0.0

    def process_transcript_segments(
        self,
        lesson_id: str,
        lesson_title: str,
        raw_segments: List[Dict[str, Any]],
        chunk_target_seconds: float = 60.0
    ) -> List[Dict[str, Any]]:
        """
        Groups Whisper segments into cohesive conceptual chunks with start/end timestamps.
        """
        chunks = []
        current_chunk_text = []
        current_start = None
        current_end = None
        chunk_idx = 0

        for seg in raw_segments:
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            text = seg.get("text", "").strip()

            if current_start is None:
                current_start = start

            current_chunk_text.append(text)
            current_end = end

            # If chunk duration reached or last segment
            if (current_end - current_start) >= chunk_target_seconds or seg == raw_segments[-1]:
                full_text = " ".join(current_chunk_text)
                chunks.append({
                    "chunk_id": f"{lesson_id}_whisper_chunk_{chunk_idx:03d}",
                    "lesson_id": lesson_id,
                    "lesson_title": lesson_title,
                    "media_type": "video_transcript",
                    "start_seconds": current_start,
                    "end_seconds": current_end,
                    "timestamp_label": f"[{self.format_timestamp(current_start)} - {self.format_timestamp(current_end)}]",
                    "text": full_text
                })
                chunk_idx += 1
                current_chunk_text = []
                current_start = None
                current_end = None

        return chunks

