"""
FHIR-inspired SQLAlchemy Data Models for City Care Clinics
Aligned with HL7 FHIR R4 Core Resources:
- Patient
- Practitioner
- Location (ClinicBranch)
- Schedule (PractitionerSchedule)
- Condition (Chronic Diseases & Allergies)
- MedicationRequest (Prescriptions)
- Appointment (Encounters)
- Observation (Lab Tests & Vitals)
- AuditEvent (AuditLog)
"""

from datetime import datetime, date, time
from typing import Optional, List
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, Time, DateTime, 
    ForeignKey, Text, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ClinicBranch(Base):
    __tablename__ = "clinic_branches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False) # e.g. "City Care Clinics - Gulberg III"
    city = Column(String(50), nullable=False) # "Lahore" or "Islamabad"
    address = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)

    practitioners = relationship("Practitioner", back_populates="primary_branch")
    schedules = relationship("PractitionerSchedule", back_populates="branch")
    appointments = relationship("Appointment", back_populates="branch")


class Practitioner(Base):
    __tablename__ = "practitioners"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(100), nullable=False) # e.g. "Dr. Ahmad Khan"
    specialty = Column(String(50), nullable=False, index=True) # General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT
    qualification = Column(String(100), nullable=False) # e.g. "MBBS, FCPS (Medicine)"
    pmdc_registration = Column(String(50), unique=True, nullable=False) # Pakistan Medical Commission Reg #
    phone = Column(String(20), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    consultation_fee = Column(Integer, nullable=False) # In PKR (e.g. 2500)
    languages_spoken = Column(String(150), default="Urdu, English, Punjabi")
    primary_branch_id = Column(String(36), ForeignKey("clinic_branches.id"), nullable=False)
    password_hash = Column(String(128), default="doctor123")
    active = Column(Boolean, default=True)

    primary_branch = relationship("ClinicBranch", back_populates="practitioners")
    schedules = relationship("PractitionerSchedule", back_populates="practitioner")
    appointments = relationship("Appointment", back_populates="practitioner")
    prescriptions = relationship("MedicationRequest", back_populates="practitioner")


class PractitionerSchedule(Base):
    __tablename__ = "practitioner_schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    practitioner_id = Column(String(36), ForeignKey("practitioners.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("clinic_branches.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 1=Tuesday, ..., 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=15)

    practitioner = relationship("Practitioner", back_populates="schedules")
    branch = relationship("ClinicBranch", back_populates="schedules")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cnic = Column(String(15), unique=True, nullable=False, index=True) # Format: 35201-1234567-1
    full_name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False) # "Male", "Female", "Other"
    date_of_birth = Column(Date, nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True) # Format: +92-300-1234567
    email = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False) # "Lahore" or "Islamabad"
    address = Column(String(255), nullable=False)
    blood_group = Column(String(5), nullable=True) # e.g. "B+", "O-"
    preferred_branch_id = Column(String(36), ForeignKey("clinic_branches.id"), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conditions = relationship("Condition", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("MedicationRequest", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="patient", cascade="all, delete-orphan")


class Condition(Base):
    """Corresponds to FHIR Condition Resource (Diagnoses & Allergy Intolerances)"""
    __tablename__ = "conditions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    category = Column(String(30), nullable=False, index=True) # "chronic_disease" or "allergy_intolerance"
    code_display = Column(String(150), nullable=False) # e.g. "Penicillin Allergy", "Type 2 Diabetes Mellitus"
    clinical_status = Column(String(20), default="active") # "active", "resolved"
    verification_status = Column(String(20), default="confirmed") # "confirmed", "provisional"
    severity = Column(String(30), default="moderate") # "mild", "moderate", "severe_anaphylaxis"
    onset_date = Column(Date, nullable=True)

    patient = relationship("Patient", back_populates="conditions")


class MedicationRequest(Base):
    """Corresponds to FHIR MedicationRequest Resource (Active & Past Prescriptions)"""
    __tablename__ = "medication_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    practitioner_id = Column(String(36), ForeignKey("practitioners.id"), nullable=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=True)
    medication_name = Column(String(100), nullable=False) # Generic name (e.g. Amoxicillin/Clavulanate)
    brand_name = Column(String(100), nullable=False, index=True) # Pakistani Brand (e.g. Augmentin)
    dosage_instruction = Column(String(150), nullable=False) # e.g. "625mg twice daily after meals"
    max_daily_dose_mg = Column(Integer, nullable=True) # e.g. 1250
    status = Column(String(20), default="active") # "active", "completed", "stopped"
    prescribed_date = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="prescriptions")
    practitioner = relationship("Practitioner", back_populates="prescriptions")
    appointment = relationship("Appointment", back_populates="prescriptions")


class Appointment(Base):
    """Corresponds to FHIR Appointment Resource (Visits & Encounters)"""
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    practitioner_id = Column(String(36), ForeignKey("practitioners.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("clinic_branches.id"), nullable=False)
    token_number = Column(String(20), unique=True, nullable=False) # e.g. "CC-104"
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="booked") # "booked", "arrived", "fulfilled", "cancelled", "rescheduled"
    appointment_type = Column(String(30), default="routine") # "routine", "urgent", "follow_up"
    chief_complaint = Column(String(255), nullable=True)
    urgency_tier = Column(String(20), default="ROUTINE") # "EMERGENCY", "URGENT", "ROUTINE"
    clinical_notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="appointments")
    practitioner = relationship("Practitioner", back_populates="appointments")
    branch = relationship("ClinicBranch", back_populates="appointments")
    prescriptions = relationship("MedicationRequest", back_populates="appointment")
    observations = relationship("Observation", back_populates="appointment")


class Observation(Base):
    """Corresponds to FHIR Observation Resource (Lab Test Values & Vitals)"""
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=True)
    category = Column(String(30), nullable=False) # "laboratory" or "vital_signs"
    code_display = Column(String(100), nullable=False, index=True) # e.g. "Platelet Count", "HbA1c", "Haemoglobin"
    value_quantity = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False) # e.g. "/mcL", "%", "g/dL", "U/L"
    reference_range = Column(String(50), nullable=False) # e.g. "150,000 - 450,000"
    interpretation = Column(String(20), nullable=False) # "normal", "high", "low", "critical"
    issued_date = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="observations")
    appointment = relationship("Appointment", back_populates="observations")


class AuditLog(Base):
    """Immutable Audit Event Log for HIPAA/Medical Regulatory Tracking"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(64), nullable=False)
    user_role = Column(String(32), nullable=False) # "PATIENT", "DOCTOR", "RECEPTIONIST", "AGENT_SUPERVISOR"
    action_type = Column(String(64), nullable=False) # "INTAKE", "PRESCRIPTION_CHECK", "EMERGENCY_HALT", "BOOKING"
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)


class PatientAgentMemory(Base):
    """
    Production-grade AI Cross-Visit Memory Store.
    Maintains clinical continuity, doctor preferences, and sanitized visit history.
    Stores NO raw CNIC, phones, or raw chat logs to maintain strict privacy compliance.
    """
    __tablename__ = "patient_agent_memories"

    patient_id = Column(String(64), primary_key=True, index=True)
    preferred_language = Column(String(20), default="UrduLish")
    preferred_doctor_id = Column(String(64), nullable=True)
    preferred_doctor_name = Column(String(100), nullable=True)
    preferred_branch = Column(String(100), nullable=True)
    last_visit_date = Column(String(20), nullable=True)
    last_complaint_summary = Column(Text, nullable=True) # PII-sanitized
    past_encounters_count = Column(Integer, default=0)
    confirmed_allergies = Column(Text, nullable=True) # JSON list
    chronic_conditions = Column(Text, nullable=True) # JSON list
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
