"""
MCP Server: patient-records
Provides secure, FHIR-aligned access to:
- Patient demographics & summary
- Documented allergies & severities
- Active medications & prescriptions
- Historical lab observations & vitals
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.mcpserver import MCPServer
from src.database.connection import db_session
from src.database.models import Patient, Condition, MedicationRequest, Observation, Appointment

server = MCPServer("patient-records")


@server.tool()
def get_patient_profile(identifier: str) -> Dict[str, Any]:
    """
    Retrieves patient demographics and chronic conditions by Patient ID, Phone, or CNIC.
    """
    session = db_session()
    try:
        patient = session.query(Patient).filter(
            (Patient.id == identifier) | 
            (Patient.phone == identifier) | 
            (Patient.cnic == identifier)
        ).first()

        if not patient:
            return {"status": "error", "message": f"Patient with identifier '{identifier}' not found."}

        conditions = [
            {"code": c.code_display, "category": c.category, "severity": c.severity}
            for c in patient.conditions
        ]

        return {
            "status": "success",
            "patient_id": patient.id,
            "full_name": patient.full_name,
            "gender": patient.gender,
            "dob": str(patient.date_of_birth),
            "phone": patient.phone,
            "cnic": patient.cnic,
            "city": patient.city,
            "address": patient.address,
            "blood_group": patient.blood_group,
            "conditions_count": len(conditions),
            "conditions": conditions
        }
    finally:
        session.close()


@server.tool()
def get_patient_allergies(patient_id: str) -> Dict[str, Any]:
    """
    Retrieves all documented drug and environmental allergies for a patient.
    """
    session = db_session()
    try:
        allergies = session.query(Condition).filter(
            Condition.patient_id == patient_id,
            Condition.category == "allergy_intolerance",
            Condition.clinical_status == "active"
        ).all()

        return {
            "status": "success",
            "patient_id": patient_id,
            "allergies_count": len(allergies),
            "allergies": [
                {
                    "allergy": a.code_display,
                    "severity": a.severity,
                    "verification": a.verification_status,
                    "onset": str(a.onset_date) if a.onset_date else "unknown"
                }
                for a in allergies
            ]
        }
    finally:
        session.close()


@server.tool()
def get_active_medications(patient_id: str) -> Dict[str, Any]:
    """
    Retrieves active prescriptions and current medicines for a patient.
    """
    session = db_session()
    try:
        meds = session.query(MedicationRequest).filter(
            MedicationRequest.patient_id == patient_id,
            MedicationRequest.status == "active"
        ).all()

        return {
            "status": "success",
            "patient_id": patient_id,
            "medications_count": len(meds),
            "medications": [
                {
                    "brand_name": m.brand_name,
                    "generic_name": m.medication_name,
                    "dosage_instruction": m.dosage_instruction,
                    "max_daily_dose_mg": m.max_daily_dose_mg,
                    "prescribed_date": str(m.prescribed_date.date()) if m.prescribed_date else "unknown"
                }
                for m in meds
            ]
        }
    finally:
        session.close()


@server.tool()
def get_lab_history(patient_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Retrieves recent laboratory test observations and vitals for a patient.
    """
    session = db_session()
    try:
        obs = session.query(Observation).filter(
            Observation.patient_id == patient_id
        ).order_by(Observation.issued_date.desc()).limit(limit).all()

        return {
            "status": "success",
            "patient_id": patient_id,
            "observations_count": len(obs),
            "observations": [
                {
                    "test_name": o.code_display,
                    "value": o.value_quantity,
                    "unit": o.unit,
                    "reference_range": o.reference_range,
                    "interpretation": o.interpretation,
                    "issued_date": str(o.issued_date.date()) if o.issued_date else "unknown"
                }
                for o in obs
            ]
        }
    finally:
        session.close()


if __name__ == "__main__":
    server.run()
