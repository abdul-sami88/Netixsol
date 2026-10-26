"""
Zarya Digital Bank - Continuous Improvement & Data Flywheel Pipeline
Week 10 - Day 5: Task 2 Feedback Processing & Flywheel Automation
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


FEEDBACK_STORE = os.path.join(os.path.dirname(__file__), "..", "data", "feedback_queue.json")
NEW_DPO_CANDIDATES = os.path.join(os.path.dirname(__file__), "..", "data", "preference", "dpo_flywheel_candidates.jsonl")


class ZaryaFeedbackFlywheel:
    """
    Continuous Improvement Flywheel:
    Ingests customer / agent feedback (thumbs down, corrections),
    filters and formats them into synthetic DPO preference triples for continuous model tuning.
    """

    def __init__(self, feedback_file: str = FEEDBACK_STORE):
        self.feedback_file = os.path.abspath(feedback_file)
        self.dpo_output_file = os.path.abspath(NEW_DPO_CANDIDATES)
        os.makedirs(os.path.dirname(self.dpo_output_file), exist_ok=True)

    def record_interaction(
        self,
        prompt: str,
        response: str,
        rating: int, # 1 = positive, 0 = negative
        corrected_response: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Records user feedback."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "response": response,
            "rating": rating,
            "corrected_response": corrected_response,
            "reason": reason
        }

        records = []
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []

        records.append(record)
        with open(self.feedback_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        # If negative rating with a correction, immediately stage as DPO candidate
        if rating == 0 and corrected_response:
            self._stage_dpo_pair(prompt, corrected_response, response, reason or "Customer negative feedback")

        return record

    def _stage_dpo_pair(self, prompt: str, chosen: str, rejected: str, category: str):
        pair = {
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "category": category,
            "source": "flywheel_feedback",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.dpo_output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    def export_retraining_dataset(self) -> int:
        """Counts and prepares candidate pairs for the bi-weekly retraining cron job."""
        if not os.path.exists(self.dpo_output_file):
            return 0
        with open(self.dpo_output_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return len(lines)


if __name__ == "__main__":
    flywheel = ZaryaFeedbackFlywheel()
    flywheel.record_interaction(
        prompt="Mera card block ho gaya hai kya karun?",
        response="Aap branch chalay jayein.",
        rating=0,
        corrected_response="Zarya Digital Bank helpline 021-111-ZARYA par call karein ya mobile app se foran unblock request generate karein.",
        reason="Vague and unhelpful guidance"
    )
    print(f"Staged DPO candidates for retraining: {flywheel.export_retraining_dataset()}")
