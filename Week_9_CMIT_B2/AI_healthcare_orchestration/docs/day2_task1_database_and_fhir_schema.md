# Week 9 Capstone: City Care Clinics
# Day 2 — Task 1: FHIR-Inspired Relational Database Schema & ER Diagram

## 1. Architectural Strategy & FHIR Alignment
To adhere to modern healthcare interoperability standards while maintaining high relational performance, the City Care Clinics database implements an HL7 FHIR (Fast Healthcare Interoperability Resources) R4-inspired schema.

### Core FHIR Resource Mapping:
| FHIR R4 Resource | Relational Table | Purpose in City Care Clinics |
| :--- | :--- | :--- |
| `Patient` | `patients` | Demographics, CNIC, Pakistani phone, primary branch, emergency contacts. |
| `Practitioner` | `practitioners` | Doctors, PMDC license #, medical specialty, fee, languages spoken. |
| `Location` | `clinic_branches` | 5 clinic branches across Lahore and Islamabad with contact and address info. |
| `Schedule` | `practitioner_schedules` | Weekly shift rosters, timings, and slot duration per doctor. |
| `Condition` | `conditions` | Medical diagnoses, chronic diseases, and documented allergy intolerances. |
| `MedicationRequest` | `medication_requests`| Active prescriptions, dosages, frequency, and treatment history. |
| `Appointment` | `appointments` | Bookings, status (Booked, Arrived, Fulfilled, Cancelled), queue tokens. |
| `Observation` | `observations` | Clinical laboratory findings (CBC, LFT, Lipid, HbA1c) and vital signs. |
| `AuditEvent` | `audit_logs` | Immutable audit trail of agent accesses, queries, and doctor approvals. |

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    PATIENT ||--o{ CONDITION : has
    PATIENT ||--o{ MEDICATION_REQUEST : prescribed
    PATIENT ||--o{ APPOINTMENT : books
    PATIENT ||--o{ OBSERVATION : undergoes
    PATIENT }o--|| CLINIC_BRANCH : preferred_branch

    PRACTITIONER ||--o{ PRACTITIONER_SCHEDULE : works_at
    PRACTITIONER ||--o{ APPOINTMENT : conducts
    PRACTITIONER ||--o{ MEDICATION_REQUEST : authorizes
    PRACTITIONER }o--|| CLINIC_BRANCH : primary_branch

    CLINIC_BRANCH ||--o{ PRACTITIONER_SCHEDULE : hosts
    CLINIC_BRANCH ||--o{ APPOINTMENT : location

    APPOINTMENT ||--o{ OBSERVATION : generates
    APPOINTMENT ||--o{ MEDICATION_REQUEST : results_in

    PATIENT {
        string id PK
        string cnic UK "13-digit Pakistani CNIC"
        string full_name
        string gender
        date date_of_birth
        string phone UK "+92-3xx-xxxxxxx"
        string email
        string city "Lahore or Islamabad"
        string address
        string blood_group
        string preferred_branch_id FK
        boolean active
        datetime created_at
    }

    PRACTITIONER {
        string id PK
        string full_name
        string specialty "General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT"
        string qualification "MBBS, FCPS, MRCP, etc."
        string pmdc_registration UK "Pakistani Medical Council Reg #"
        string phone
        string email UK
        int consultation_fee "PKR"
        string languages_spoken "Urdu, English, Punjabi"
        string primary_branch_id FK
        boolean active
    }

    CLINIC_BRANCH {
        string id PK
        string name "e.g., Gulberg Branch, F-8 Branch"
        string city "Lahore or Islamabad"
        string address
        string phone
        string email
    }

    PRACTITIONER_SCHEDULE {
        string id PK
        string practitioner_id FK
        string branch_id FK
        int day_of_week "0=Monday to 6=Sunday"
        time start_time
        time end_time
        int slot_duration_minutes "Default 15 min"
    }

    CONDITION {
        string id PK
        string patient_id FK
        string category "chronic_disease | allergy_intolerance"
        string code_display "e.g., Diabetes Type 2, Penicillin Allergy"
        string clinical_status "active | resolved"
        string verification_status "confirmed | provisional"
        string severity "mild | moderate | severe_anaphylaxis"
        date onset_date
    }

    MEDICATION_REQUEST {
        string id PK
        string patient_id FK
        string practitioner_id FK
        string appointment_id FK
        string medication_name "Generic e.g., Amoxicillin"
        string brand_name "Local Brand e.g., Augmentin"
        string dosage_instruction "e.g., 625mg twice daily after meals"
        int max_daily_dose_mg
        string status "active | completed | stopped"
        datetime prescribed_date
    }

    APPOINTMENT {
        string id PK
        string patient_id FK
        string practitioner_id FK
        string branch_id FK
        string token_number UK "e.g., CC-104"
        datetime start_time
        datetime end_time
        string status "booked | arrived | fulfilled | cancelled | rescheduled"
        string appointment_type "routine | urgent | follow_up"
        string chief_complaint
        string urgency_tier "EMERGENCY | URGENT | ROUTINE"
        text clinical_notes
    }

    OBSERVATION {
        string id PK
        string patient_id FK
        string appointment_id FK
        string category "laboratory | vital_signs"
        string code_display "e.g., Platelet Count, HbA1c, Blood Pressure"
        float value_quantity
        string unit "e.g., /mcL, %, mg/dL, mmHg"
        string reference_range "e.g., 150000 - 450000"
        string interpretation "normal | high | low | critical"
        datetime issued_date
    }
```

---

## 3. Key Schema Design Decisions
1. **Pakistani Localization First:**
   - Explicit storage for 13-digit Pakistani CNIC (`35201-xxxxxxx-x`) and phone format (`+92-3xx-xxxxxxx`).
   - Branch mapping across 5 physical clinics in Lahore (*Gulberg III, DHA Phase 5, Johar Town*) and Islamabad (*F-8 Markaz, Blue Area*).
   - PMDC (Pakistan Medical & Dental Council) registration number enforced for all 30 doctors.
2. **Clinical Safety Decoupling:**
   - Allergies and chronic conditions are stored in `conditions` with explicit `category` (`allergy_intolerance` vs `chronic_disease`) and `severity` fields. This allows the **Prescription Safety Agent** to run sub-millisecond indexed lookups before clearing medications.
3. **Flexible Storage Driver:**
   - Compatible natively with both **PostgreSQL (Supabase / Render)** and local **SQLite** via SQLAlchemy 2.0 ORM, guaranteeing zero-crash operation in both development and production cloud environments.
