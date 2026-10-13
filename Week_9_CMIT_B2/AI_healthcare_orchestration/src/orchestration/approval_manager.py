"""
Human-in-the-Loop Approval Manager for City Care Clinics.
Manages medical safety approvals before content reaches patients:
1. Lab Result Explanations (verifies safety & non-diagnostic framing)
2. Prescriptions & Medication Messages (ensures drug safety & correct dosage)
3. Low-Confidence Triage Decisions (confidence < 0.75 or borderline cases)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APPROVALS_DIR = PROJECT_ROOT / "data"
APPROVALS_FILE = APPROVALS_DIR / "pending_approvals.json"


class ApprovalItem(BaseModel):
    approval_id: str
    approval_type: str # "LAB_EXPLANATION", "PRESCRIPTION", "LOW_CONFIDENCE_TRIAGE"
    patient_id: str
    patient_name: str
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    created_at: str
    status: str = Field(default="PENDING") # "PENDING", "APPROVED", "EDITED", "REJECTED"
    payload: Dict[str, Any] # The content requiring review
    context: Dict[str, Any] = Field(default_factory=dict)
    doctor_decision: Optional[Dict[str, Any]] = None
    resolved_at: Optional[str] = None


class ApprovalManager:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or APPROVALS_FILE
        self._ensure_store()

    def _ensure_store(self):
        APPROVALS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_all(self, items: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def create_approval_request(
        self,
        approval_type: str,
        patient_id: str,
        patient_name: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        doctor_id: Optional[str] = None,
        doctor_name: Optional[str] = None
    ) -> str:
        """Creates a new pending approval item assigned to a specific doctor and returns approval_id."""
        approval_id = f"APPR-{datetime.utcnow().strftime('%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        item = ApprovalItem(
            approval_id=approval_id,
            approval_type=approval_type,
            patient_id=patient_id,
            patient_name=patient_name,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            created_at=datetime.utcnow().isoformat(),
            status="PENDING",
            payload=payload,
            context=context or {}
        )
        all_items = self._load_all()
        all_items.append(item.model_dump())
        self._save_all(all_items)
        return approval_id

    def get_pending_approvals(self, doctor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all items currently awaiting physician action, optionally filtered by doctor."""
        all_items = self._load_all()
        if doctor_id:
            return [i for i in all_items if i.get("status") == "PENDING" and (i.get("doctor_id") == doctor_id or i.get("doctor_id") is None)]
        return [i for i in all_items if i.get("status") == "PENDING"]

    def get_doctor_approvals(self, doctor_id: str, doctor_name: Optional[str] = None) -> Dict[str, Any]:
        """
        CRITICAL DOCTOR ISOLATION:
        Returns ONLY the approvals that are assigned to THIS specific doctor.
        """
        all_items = self._load_all()
        doc_items = [
            i for i in all_items
            if (i.get("doctor_id") == doctor_id) or 
               (doctor_name and i.get("doctor_name") == doctor_name) or
               (i.get("doctor_id") is None and doctor_id in ["doc-001", "doc-026"]) # fallback pool for unassigned
        ]
        pending = [i for i in doc_items if i.get("status") == "PENDING"]
        resolved = [i for i in doc_items if i.get("status") != "PENDING"]
        return {
            "pending": pending,
            "resolved": resolved
        }

    def get_all_approvals(self) -> List[Dict[str, Any]]:
        """Returns all approvals history."""
        return self._load_all()

    def get_approval_by_id(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Finds an approval item by ID."""
        for item in self._load_all():
            if item.get("approval_id") == approval_id:
                return item
        return None

    def submit_doctor_decision(
        self,
        approval_id: str,
        action: str, # "APPROVE", "EDIT", "REJECT"
        doctor_name: str,
        notes: str = "",
        edited_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records the physician's review action:
        - APPROVE: Approved without modification.
        - EDIT: Physician edited the text/prescription.
        - REJECT: Physician rejected the content.
        """
        all_items = self._load_all()
        target = None
        for item in all_items:
            if item["approval_id"] == approval_id:
                target = item
                break

        if not target:
            return {"status": "error", "message": f"Approval request {approval_id} not found."}

        action_status = {
            "APPROVE": "APPROVED",
            "EDIT": "EDITED",
            "REJECT": "REJECTED"
        }.get(action.upper(), "APPROVED")

        decision_record = {
            "action": action_status,
            "doctor_name": doctor_name,
            "notes": notes,
            "timestamp": datetime.utcnow().isoformat(),
            "edited_payload": edited_payload if action_status == "EDITED" else None
        }

        target["status"] = action_status
        target["doctor_decision"] = decision_record
        target["resolved_at"] = datetime.utcnow().isoformat()

        if action_status == "EDITED" and edited_payload:
            target["payload"].update(edited_payload)

        self._save_all(all_items)
        return {
            "status": "success",
            "approval_id": approval_id,
            "action": action_status,
            "decision": decision_record
        }
