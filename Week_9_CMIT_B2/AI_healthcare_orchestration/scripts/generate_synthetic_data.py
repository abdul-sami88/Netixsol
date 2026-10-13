"""
Comprehensive Synthetic Data Generation & Seeding Script for City Care Clinics
Generates:
- 5 Clinic Branches in Lahore & Islamabad
- 30 Doctors across 6 specialties with weekly schedules & PMDC licenses
- 500 Pakistani patients with authentic names, CNICs, phone numbers, and addresses
- Correlated conditions (chronic diseases & allergy test cases like Penicillin)
- 100 Common Pakistani brand medicines linked with indications and max dosages
- Realistic historical & upcoming appointments with tokens
- 500+ Correlated clinical lab observations (CBC, LFT, Lipid, HbA1c, Vitals)
"""

import sys
import os
import random
from datetime import datetime, date, time, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from faker import Faker
from src.database.connection import init_db, db_session
from src.database.models import (
    ClinicBranch, Practitioner, PractitionerSchedule, Patient, 
    Condition, MedicationRequest, Appointment, Observation, AuditLog
)

fake = Faker()
random.seed(42)

# --- 1. REFERENCE DATA DEFINITIONS ---

BRANCHES_DATA = [
    {
        "id": "branch-lahore-gulberg",
        "name": "City Care Clinics - Main Gulberg",
        "city": "Lahore",
        "address": "Plot 14-C, Main Boulevard, Gulberg III, Lahore",
        "phone": "+92-42-35750011",
        "email": "gulberg@citycareclinics.pk"
    },
    {
        "id": "branch-lahore-dha",
        "name": "City Care Clinics - DHA Phase 5",
        "city": "Lahore",
        "address": "Plaza 88, Commercial Broadway, DHA Phase 5, Lahore",
        "phone": "+92-42-35890022",
        "email": "dha@citycareclinics.pk"
    },
    {
        "id": "branch-lahore-johar",
        "name": "City Care Clinics - Johar Town",
        "city": "Lahore",
        "address": "45-G, G-Block Commercial, Johar Town, Lahore",
        "phone": "+92-42-35200033",
        "email": "johartown@citycareclinics.pk"
    },
    {
        "id": "branch-islamabad-f8",
        "name": "City Care Clinics - F-8 Markaz",
        "city": "Islamabad",
        "address": "Executive Center, Ayub Market, F-8 Markaz, Islamabad",
        "phone": "+92-51-2250044",
        "email": "f8@citycareclinics.pk"
    },
    {
        "id": "branch-islamabad-bluearea",
        "name": "City Care Clinics - Blue Area",
        "city": "Islamabad",
        "address": "State Life Building #5, Jinnah Avenue, Blue Area, Islamabad",
        "phone": "+92-51-2800055",
        "email": "bluearea@citycareclinics.pk"
    }
]

SPECIALTIES = [
    "General Medicine",
    "Paediatrics",
    "Gynaecology",
    "Cardiology",
    "Dermatology",
    "ENT"
]

DOCTOR_NAMES_BY_SPECIALTY = {
    "General Medicine": [
        ("Dr. Ahmad Khan", "Male", "MBBS, FCPS (Medicine)"),
        ("Dr. Ayesha Siddiqa", "Female", "MBBS, MRCP (UK)"),
        ("Dr. Tariq Mahmood", "Male", "MBBS, MCPS"),
        ("Dr. Hina Rizvi", "Female", "MBBS, FCPS (Internal Medicine)"),
        ("Dr. Bilal Aslam", "Male", "MBBS, MD")
    ],
    "Paediatrics": [
        ("Dr. Fatima Zahra", "Female", "MBBS, FCPS (Paediatrics)"),
        ("Dr. Usman Ghani", "Male", "MBBS, DCH, MRCPCH"),
        ("Dr. Maryam Noor", "Female", "MBBS, MCPS (Paeds)"),
        ("Dr. Hamza Ali", "Male", "MBBS, FCPS (Paediatrics)"),
        ("Dr. Sadia Bashir", "Female", "MBBS, FCPS (Neonatology)")
    ],
    "Gynaecology": [
        ("Dr. Farzana Malik", "Female", "MBBS, FCPS (Obs & Gynae)"),
        ("Dr. Shazia Parveen", "Female", "MBBS, MRCOG (UK)"),
        ("Dr. Naila Kausar", "Female", "MBBS, FCPS"),
        ("Dr. Rabia Zafar", "Female", "MBBS, MCPS"),
        ("Dr. Tahira Yasmin", "Female", "MBBS, FCPS (Obs & Gynae)")
    ],
    "Cardiology": [
        ("Dr. Kamran Qureshi", "Male", "MBBS, FCPS (Cardiology)"),
        ("Dr. Shahzad Rasheed", "Male", "MBBS, MRCP, FACC"),
        ("Dr. Zainab Bokhari", "Female", "MBBS, FCPS (Interventional Cardiology)"),
        ("Dr. Asim Jamil", "Male", "MBBS, Diplomate American Board Cardiology"),
        ("Dr. Faisal Munir", "Male", "MBBS, FCPS (Cardiology)")
    ],
    "Dermatology": [
        ("Dr. Sara Malik", "Female", "MBBS, FCPS (Dermatology)"),
        ("Dr. Imran Waheed", "Male", "MBBS, Dip Derm (Glasgow)"),
        ("Dr. Mahnoor Javed", "Female", "MBBS, MCPS (Dermatology)"),
        ("Dr. Omer Farooq", "Male", "MBBS, FCPS (Dermatology)"),
        ("Dr. Saira Bano", "Female", "MBBS, MSc Dermatology (UK)")
    ],
    "ENT": [
        ("Dr. Haris Nadeem", "Male", "MBBS, FCPS (Oto-Rhino-Laryngology)"),
        ("Dr. Bushra Rehman", "Female", "MBBS, DLO, FCPS"),
        ("Dr. Adnan Latif", "Male", "MBBS, FRCS (ENT)"),
        ("Dr. Nadia Afzal", "Female", "MBBS, FCPS (ENT)"),
        ("Dr. Waqas Cheema", "Male", "MBBS, MCPS (ENT)")
    ]
}

# 100 Common Pakistani Medicines with Brand, Generic, Class, & Max Dose
PAKISTAN_MEDICATIONS = [
    # Analgesics & Antipyretics
    {"brand": "Panadol", "generic": "Paracetamol", "dose_inst": "500mg every 6 hours as needed", "max_dose": 4000, "class": "Analgesic"},
    {"brand": "Panadol Extra", "generic": "Paracetamol + Caffeine", "dose_inst": "500/65mg every 8 hours", "max_dose": 4000, "class": "Analgesic"},
    {"brand": "Calpol Syrup", "generic": "Paracetamol", "dose_inst": "120mg/5ml, 5ml three times daily", "max_dose": 2000, "class": "Analgesic"},
    {"brand": "Disprin", "generic": "Aspirin (Acetylsalicylic Acid)", "dose_inst": "300mg dissolved in water", "max_dose": 3000, "class": "NSAID"},
    {"brand": "Loprin", "generic": "Low-dose Aspirin", "dose_inst": "75mg once daily after lunch", "max_dose": 150, "class": "Antiplatelet"},
    {"brand": "Brufen", "generic": "Ibuprofen", "dose_inst": "400mg twice daily after meals", "max_dose": 2400, "class": "NSAID"},
    {"brand": "Arinac", "generic": "Ibuprofen + Pseudoephedrine", "dose_inst": "1 tablet twice daily", "max_dose": 4, "class": "Decongestant/NSAID"},
    {"brand": "Ponstan", "generic": "Mefenamic Acid", "dose_inst": "500mg three times daily after meals", "max_dose": 1500, "class": "NSAID"},
    {"brand": "Voltral", "generic": "Diclofenac Sodium", "dose_inst": "50mg twice daily after meals", "max_dose": 150, "class": "NSAID"},
    {"brand": "Ansaid", "generic": "Flurbiprofen", "dose_inst": "100mg twice daily", "max_dose": 300, "class": "NSAID"},
    {"brand": "Toradol", "generic": "Ketorolac Tromethamine", "dose_inst": "10mg every 6 hours for max 5 days", "max_dose": 40, "class": "NSAID"},
    {"brand": "Celebrex", "generic": "Celecoxib", "dose_inst": "200mg once daily", "max_dose": 400, "class": "COX-2 Inhibitor"},
    {"brand": "Synflex", "generic": "Naproxen Sodium", "dose_inst": "550mg twice daily", "max_dose": 1100, "class": "NSAID"},
    {"brand": "Tramal", "generic": "Tramadol HCl", "dose_inst": "50mg twice daily as needed", "max_dose": 400, "class": "Opioid Analgesic"},
    
    # Antibiotics & Anti-infectives
    {"brand": "Augmentin", "generic": "Amoxicillin + Clavulanic Acid", "dose_inst": "625mg twice daily for 7 days", "max_dose": 2000, "class": "Penicillin Antibiotic"},
    {"brand": "Augmentin 1g", "generic": "Amoxicillin + Clavulanic Acid", "dose_inst": "1000mg twice daily for 7 days", "max_dose": 2000, "class": "Penicillin Antibiotic"},
    {"brand": "Amoxil", "generic": "Amoxicillin", "dose_inst": "500mg three times daily", "max_dose": 3000, "class": "Penicillin Antibiotic"},
    {"brand": "Ampiclox", "generic": "Ampicillin + Cloxacillin", "dose_inst": "500mg four times daily", "max_dose": 4000, "class": "Penicillin Antibiotic"},
    {"brand": "Cravit", "generic": "Levofloxacin", "dose_inst": "500mg once daily for 7 days", "max_dose": 750, "class": "Fluoroquinolone"},
    {"brand": "Ciprobid", "generic": "Ciprofloxacin", "dose_inst": "500mg twice daily for 5 days", "max_dose": 1500, "class": "Fluoroquinolone"},
    {"brand": "Avelox", "generic": "Moxifloxacin", "dose_inst": "400mg once daily", "max_dose": 400, "class": "Fluoroquinolone"},
    {"brand": "Klaricid", "generic": "Clarithromycin", "dose_inst": "500mg twice daily for 10 days", "max_dose": 1000, "class": "Macrolide"},
    {"brand": "Azomax", "generic": "Azithromycin", "dose_inst": "500mg once daily for 3 days", "max_dose": 500, "class": "Macrolide"},
    {"brand": "Zithrokan", "generic": "Azithromycin", "dose_inst": "250mg once daily", "max_dose": 500, "class": "Macrolide"},
    {"brand": "Cefspan", "generic": "Cefixime", "dose_inst": "400mg once daily for 5 days", "max_dose": 800, "class": "Cephalosporin"},
    {"brand": "Rocephin", "generic": "Ceftriaxone", "dose_inst": "1g IM/IV once daily", "max_dose": 2000, "class": "Cephalosporin"},
    {"brand": "Velosef", "generic": "Cephradine", "dose_inst": "500mg four times daily", "max_dose": 4000, "class": "Cephalosporin"},
    {"brand": "Ceporex", "generic": "Cephalexin", "dose_inst": "500mg every 6 hours", "max_dose": 4000, "class": "Cephalosporin"},
    {"brand": "Flagyl", "generic": "Metronidazole", "dose_inst": "400mg three times daily for 5 days", "max_dose": 1500, "class": "Nitroimidazole"},
    {"brand": "Entamizole", "generic": "Metronidazole + Diloxanide Furoate", "dose_inst": "1 tablet three times daily", "max_dose": 3, "class": "Antiamoebic"},
    {"brand": "Septran", "generic": "Co-trimoxazole (Sulfamethoxazole + Trimethoprim)", "dose_inst": "960mg twice daily", "max_dose": 1920, "class": "Sulfonamide Antibiotic"},
    {"brand": "Vibramycin", "generic": "Doxycycline", "dose_inst": "100mg once daily after meal", "max_dose": 200, "class": "Tetracycline"},
    {"brand": "Fucidin", "generic": "Fusidic Acid", "dose_inst": "Apply cream twice daily topically", "max_dose": 0, "class": "Topical Antibacterial"},

    # Gastrointestinal & Acid Reducers
    {"brand": "Risek", "generic": "Omeprazole", "dose_inst": "20mg once daily before breakfast", "max_dose": 40, "class": "PPI"},
    {"brand": "Risek Insta", "generic": "Omeprazole + Sodium Bicarbonate", "dose_inst": "20mg sachet once daily", "max_dose": 40, "class": "PPI"},
    {"brand": "Nexum", "generic": "Esomeprazole", "dose_inst": "40mg once daily before breakfast", "max_dose": 80, "class": "PPI"},
    {"brand": "Zopent", "generic": "Pantoprazole", "dose_inst": "40mg once daily before meals", "max_dose": 80, "class": "PPI"},
    {"brand": "Getzome", "generic": "Omeprazole", "dose_inst": "40mg once daily", "max_dose": 40, "class": "PPI"},
    {"brand": "Gravinate", "generic": "Dimenhydrinate", "dose_inst": "50mg as needed for nausea", "max_dose": 300, "class": "Antiemetic"},
    {"brand": "Motilium", "generic": "Domperidone", "dose_inst": "10mg three times daily before meals", "max_dose": 30, "class": "Prokinetic"},
    {"brand": "Maxolon", "generic": "Metoclopramide", "dose_inst": "10mg three times daily", "max_dose": 30, "class": "Antiemetic"},
    {"brand": "Gaviscon Liquid", "generic": "Sodium Alginate + Potassium Bicarbonate", "dose_inst": "10ml after meals and at bedtime", "max_dose": 40, "class": "Antacid"},
    {"brand": "Mucaine", "generic": "Oxethazaine + Antacids", "dose_inst": "10ml 15 min before meals", "max_dose": 40, "class": "Antacid/Anesthetic"},
    {"brand": "Spasfon", "generic": "Phloroglucinol", "dose_inst": "1 tablet as needed for cramps", "max_dose": 6, "class": "Antispasmodic"},
    {"brand": "Buscopan", "generic": "Hyoscine Butylbromide", "dose_inst": "10mg three times daily for spasms", "max_dose": 60, "class": "Antispasmodic"},
    {"brand": "Colofac", "generic": "Mebeverine HCl", "dose_inst": "135mg three times daily before meals", "max_dose": 405, "class": "Antispasmodic"},
    {"brand": "Duphalac", "generic": "Lactulose", "dose_inst": "15ml twice daily", "max_dose": 60, "class": "Laxative"},
    {"brand": "Imodium", "generic": "Loperamide", "dose_inst": "2mg after each loose stool", "max_dose": 16, "class": "Antidiarrheal"},

    # Cardiovascular & Antihypertensives
    {"brand": "Concor", "generic": "Bisoprolol Fumarate", "dose_inst": "5mg once daily in morning", "max_dose": 10, "class": "Beta Blocker"},
    {"brand": "Concor Cor", "generic": "Bisoprolol Fumarate", "dose_inst": "2.5mg once daily", "max_dose": 10, "class": "Beta Blocker"},
    {"brand": "Inderal", "generic": "Propranolol HCl", "dose_inst": "10mg twice daily", "max_dose": 160, "class": "Beta Blocker"},
    {"brand": "Norvasc", "generic": "Amlodipine Besylate", "dose_inst": "5mg once daily", "max_dose": 10, "class": "Calcium Channel Blocker"},
    {"brand": "Softvasc", "generic": "Amlodipine", "dose_inst": "10mg once daily", "max_dose": 10, "class": "Calcium Channel Blocker"},
    {"brand": "Capoten", "generic": "Captopril", "dose_inst": "25mg twice daily", "max_dose": 150, "class": "ACE Inhibitor"},
    {"brand": "Zestril", "generic": "Lisinopril", "dose_inst": "10mg once daily", "max_dose": 40, "class": "ACE Inhibitor"},
    {"brand": "Cozaar", "generic": "Losartan Potassium", "dose_inst": "50mg once daily", "max_dose": 100, "class": "ARB"},
    {"brand": "Hyzaar", "generic": "Losartan + Hydrochlorothiazide", "dose_inst": "50/12.5mg once daily", "max_dose": 100, "class": "ARB/Diuretic"},
    {"brand": "Diovan", "generic": "Valsartan", "dose_inst": "80mg once daily", "max_dose": 320, "class": "ARB"},
    {"brand": "Exforge", "generic": "Amlodipine + Valsartan", "dose_inst": "5/80mg once daily", "max_dose": 10, "class": "CCB/ARB"},
    {"brand": "Lasix", "generic": "Furosemide", "dose_inst": "40mg once daily morning", "max_dose": 80, "class": "Loop Diuretic"},
    {"brand": "Spiromide", "generic": "Spironolactone + Furosemide", "dose_inst": "50/20mg once daily", "max_dose": 100, "class": "Diuretic Combo"},
    {"brand": "Aldactone", "generic": "Spironolactone", "dose_inst": "25mg once daily", "max_dose": 100, "class": "Potassium-sparing Diuretic"},
    {"brand": "Lipitor", "generic": "Atorvastatin Calcium", "dose_inst": "20mg at bedtime", "max_dose": 80, "class": "Statin"},
    {"brand": "Atorva", "generic": "Atorvastatin", "dose_inst": "10mg at bedtime", "max_dose": 80, "class": "Statin"},
    {"brand": "Crestor", "generic": "Rosuvastatin Calcium", "dose_inst": "10mg at bedtime", "max_dose": 40, "class": "Statin"},
    {"brand": "Roseday", "generic": "Rosuvastatin", "dose_inst": "5mg at bedtime", "max_dose": 40, "class": "Statin"},
    {"brand": "Plavix", "generic": "Clopidogrel", "dose_inst": "75mg once daily", "max_dose": 75, "class": "Antiplatelet"},
    {"brand": "Angised", "generic": "Glyceryl Trinitrate (GTN)", "dose_inst": "0.5mg sublingual as needed for angina", "max_dose": 3, "class": "Nitrate"},

    # Diabetes & Endocrine
    {"brand": "Glucophage", "generic": "Metformin HCl", "dose_inst": "500mg twice daily with meals", "max_dose": 2000, "class": "Biguanide"},
    {"brand": "Glucophage XR", "generic": "Metformin Extended Release", "dose_inst": "1000mg once daily with dinner", "max_dose": 2000, "class": "Biguanide"},
    {"brand": "Getryl", "generic": "Glimepiride", "dose_inst": "2mg once daily before breakfast", "max_dose": 8, "class": "Sulfonylurea"},
    {"brand": "Amaryl", "generic": "Glimepiride", "dose_inst": "1mg once daily", "max_dose": 8, "class": "Sulfonylurea"},
    {"brand": "Diamicron MR", "generic": "Gliclazide Modified Release", "dose_inst": "60mg with breakfast", "max_dose": 120, "class": "Sulfonylurea"},
    {"brand": "Januvia", "generic": "Sitagliptin", "dose_inst": "100mg once daily", "max_dose": 100, "class": "DPP-4 Inhibitor"},
    {"brand": "Janumet", "generic": "Sitagliptin + Metformin", "dose_inst": "50/500mg twice daily", "max_dose": 2, "class": "DPP-4/Biguanide"},
    {"brand": "Galvus Met", "generic": "Vildagliptin + Metformin", "dose_inst": "50/850mg twice daily", "max_dose": 2, "class": "DPP-4/Biguanide"},
    {"brand": "Jardiance", "generic": "Empagliflozin", "dose_inst": "10mg once daily morning", "max_dose": 25, "class": "SGLT2 Inhibitor"},
    {"brand": "Thyroxine", "generic": "Levothyroxine Sodium", "dose_inst": "50mcg once daily empty stomach", "max_dose": 200, "class": "Thyroid Hormone"},

    # Respiratory & Allergy
    {"brand": "Softin", "generic": "Loratadine", "dose_inst": "10mg once daily at night", "max_dose": 10, "class": "Antihistamine"},
    {"brand": "Telfast", "generic": "Fexofenadine HCl", "dose_inst": "120mg once daily", "max_dose": 180, "class": "Antihistamine"},
    {"brand": "Zyrtec", "generic": "Cetirizine HCl", "dose_inst": "10mg once daily", "max_dose": 10, "class": "Antihistamine"},
    {"brand": "Rigix", "generic": "Cetirizine", "dose_inst": "10mg at bedtime", "max_dose": 10, "class": "Antihistamine"},
    {"brand": "Kestine", "generic": "Ebastine", "dose_inst": "10mg once daily", "max_dose": 20, "class": "Antihistamine"},
    {"brand": "Ventolin Inhaler", "generic": "Salbutamol", "dose_inst": "2 puffs as needed for wheezing", "max_dose": 8, "class": "Short-acting Beta Agonist"},
    {"brand": "Seretide Evohaler", "generic": "Salmeterol + Fluticasone", "dose_inst": "2 puffs twice daily", "max_dose": 4, "class": "ICS/LABA"},
    {"brand": "Symbicort Turbuhaler", "generic": "Budesonide + Formoterol", "dose_inst": "160/4.5mcg twice daily", "max_dose": 4, "class": "ICS/LABA"},
    {"brand": "Myteka", "generic": "Montelukast Sodium", "dose_inst": "10mg at night", "max_dose": 10, "class": "Leukotriene Receptor Antagonist"},
    {"brand": "Montec", "generic": "Montelukast", "dose_inst": "10mg once daily", "max_dose": 10, "class": "Leukotriene Receptor Antagonist"},
    {"brand": "Hydryllin Syrup", "generic": "Aminophylline + Diphenhydramine", "dose_inst": "10ml three times daily for cough", "max_dose": 30, "class": "Cough Expectorant"},
    {"brand": "Pulmonol Syrup", "generic": "Dextromethorphan + Chlorpheniramine", "dose_inst": "10ml twice daily", "max_dose": 30, "class": "Cough Suppressant"},

    # Dermatology & Topical
    {"brand": "Dermovate", "generic": "Clobetasol Propionate", "dose_inst": "Apply thin layer once daily", "max_dose": 0, "class": "Potent Corticosteroid"},
    {"brand": "Hydrozole Cream", "generic": "Hydrocortisone + Clotrimazole", "dose_inst": "Apply twice daily for 7 days", "max_dose": 0, "class": "Antifungal/Steroid"},
    {"brand": "Travocort", "generic": "Isoconazole + Diflucortolone", "dose_inst": "Apply twice daily", "max_dose": 0, "class": "Antifungal/Steroid"},
    {"brand": "Betnovate", "generic": "Betamethasone Valerate", "dose_inst": "Apply thin film twice daily", "max_dose": 0, "class": "Topical Corticosteroid"},
    {"brand": "Polyfax Ointment", "generic": "Polymyxin B + Bacitracin", "dose_inst": "Apply twice daily to cuts/burns", "max_dose": 0, "class": "Topical Antibiotic"},
    {"brand": "Skinoren Cream", "generic": "Azelaic Acid", "dose_inst": "Apply twice daily for acne", "max_dose": 0, "class": "Acne Agent"},
    {"brand": "Canesten Cream", "generic": "Clotrimazole", "dose_inst": "Apply two to three times daily", "max_dose": 0, "class": "Antifungal"},

    # ENT Specific
    {"brand": "Otrivin Nasal Drops", "generic": "Xylometazoline HCl", "dose_inst": "2 drops in each nostril max 5 days", "max_dose": 3, "class": "Nasal Decongestant"},
    {"brand": "Nasonex Nasal Spray", "generic": "Mometasone Furoate", "dose_inst": "2 sprays in each nostril daily", "max_dose": 2, "class": "Nasal Corticosteroid"},
    {"brand": "Beclodual", "generic": "Beclomethasone Dipropionate", "dose_inst": "1 spray each nostril twice daily", "max_dose": 4, "class": "Nasal Corticosteroid"},
    {"brand": "Waxsol Ear Drops", "generic": "Docusate Sodium", "dose_inst": "Fill ear at bedtime for 2 consecutive nights", "max_dose": 0, "class": "Ceruminolytic"}
]

PAKISTANI_FIRST_NAMES_MALE = [
    "Muhammad", "Ali", "Ahmad", "Usman", "Bilal", "Tariq", "Hamza", "Zain", 
    "Omer", "Hassan", "Hussain", "Kashif", "Waqas", "Babar", "Shoaib", 
    "Shahid", "Asif", "Nasir", "Kamran", "Faisal", "Imran", "Farhan"
]

PAKISTANI_FIRST_NAMES_FEMALE = [
    "Fatima", "Ayesha", "Zainab", "Maryam", "Sana", "Hira", "Sadia", "Khadija", 
    "Amna", "Mahnoor", "Rabia", "Bushra", "Nadia", "Sobia", "Iqra", "Zunaira", 
    "Anam", "Sidra", "Farah", "Sumera", "Nazia", "Marium"
]

PAKISTANI_LAST_NAMES = [
    "Khan", "Malik", "Chaudhry", "Bhatti", "Raza", "Sheikh", "Qureshi", 
    "Siddiqui", "Ansari", "Mirza", "Shah", "Abbasi", "Butt", "Jutt", 
    "Awan", "Hashmi", "Gondal", "Mughal", "Niazi", "Rehman", "Aziz"
]

LAHORE_AREAS = [
    "Gulberg III", "DHA Phase 5", "Johar Town Phase 1", "Model Town Block C", 
    "Faisal Town", "Wapda Town", "Bahria Town Sector C", "Garden Town", 
    "Shadman Colony", "Cavalry Ground"
]

ISLAMABAD_AREAS = [
    "Sector F-8/2", "Sector F-7/4", "Sector F-10/3", "Sector G-9/1", 
    "Sector G-11/2", "Sector I-8/4", "Blue Area", "DHA Phase 2", 
    "Bahria Town Phase 4", "PWD Housing Society"
]


def generate_cnic(gender: str, city: str) -> str:
    # 35201 for Lahore, 61101 for Islamabad
    dist = "35201" if city == "Lahore" else "61101"
    mid = f"{random.randint(1000000, 9999999)}"
    # Odd for male, even for female
    last_digit = random.choice([1, 3, 5, 7, 9]) if gender == "Male" else random.choice([2, 4, 6, 8])
    return f"{dist}-{mid}-{last_digit}"


def generate_phone() -> str:
    prefix = random.choice(["0300", "0301", "0302", "0321", "0322", "0333", "0334", "0345", "0346"])
    suffix = random.randint(1000000, 9999999)
    return f"+92-{prefix[1:]}-{suffix}"


# --- 2. SEEDING LOGIC ---

def seed_database():
    print("=" * 70)
    print("Initializing City Care Clinics FHIR-inspired Database...")
    print("=" * 70)

    # Initialize tables
    init_db()
    session = db_session()

    # Clear existing data cleanly if re-running
    print("Clearing prior records to maintain referential integrity...")
    session.query(AuditLog).delete()
    session.query(Observation).delete()
    session.query(MedicationRequest).delete()
    session.query(Condition).delete()
    session.query(Appointment).delete()
    session.query(Patient).delete()
    session.query(PractitionerSchedule).delete()
    session.query(Practitioner).delete()
    session.query(ClinicBranch).delete()
    session.commit()

    # 1. Seed Branches
    print("\n1. Seeding 5 Clinic Branches in Lahore & Islamabad...")
    branches = []
    for b_data in BRANCHES_DATA:
        branch = ClinicBranch(**b_data)
        session.add(branch)
        branches.append(branch)
    session.commit()
    print(f"   Successfully added {len(branches)} branches.")

    # 2. Seed 30 Doctors across 6 Specialties
    print("\n2. Seeding 30 Doctors & Weekly Rosters across 6 Specialties...")
    practitioners = []
    pmdc_counter = 10001
    
    for specialty, doc_list in DOCTOR_NAMES_BY_SPECIALTY.items():
        for i, (doc_name, gender, qual) in enumerate(doc_list):
            branch = branches[(len(practitioners)) % len(branches)]
            email_slug = doc_name.lower().replace("dr. ", "").replace(" ", ".")
            
            practitioner = Practitioner(
                id=f"doc-{len(practitioners)+1:03d}",
                full_name=doc_name,
                specialty=specialty,
                qualification=qual,
                pmdc_registration=f"PMDC-{pmdc_counter}-P",
                phone=generate_phone(),
                email=f"{email_slug}@citycareclinics.pk",
                consultation_fee=random.choice([2000, 2500, 3000, 3500]),
                languages_spoken="Urdu, English, Punjabi",
                primary_branch_id=branch.id,
                active=True
            )
            session.add(practitioner)
            practitioners.append(practitioner)
            pmdc_counter += 1

            # Seed Schedules (Mon-Fri or Mon-Sat)
            # Two shifts: Morning 09:00-13:00 or Evening 16:00-20:00
            is_evening = (i % 2 == 1)
            start_t = time(16, 0) if is_evening else time(9, 0)
            end_t = time(20, 0) if is_evening else time(13, 0)

            for day in range(0, 6): # Mon to Sat
                schedule = PractitionerSchedule(
                    practitioner_id=practitioner.id,
                    branch_id=branch.id,
                    day_of_week=day,
                    start_time=start_t,
                    end_time=end_t,
                    slot_duration_minutes=15
                )
                session.add(schedule)

    session.commit()
    print(f"   Successfully added {len(practitioners)} doctors with weekly schedules.")

    # 3. Seed 500 Synthetic Patients with Clinical Profiles
    print("\n3. Seeding 500 Patients with Clinical Profiles & Correlated Conditions...")
    patients = []
    
    # Pre-select index slots for crucial clinical safety evaluation test-cases
    # e.g., Penicillin allergy patients, Diabetic patients, Hypertension patients
    used_cnics = set()
    used_phones = set()

    for p_idx in range(500):
        gender = "Male" if random.random() < 0.48 else "Female"
        first_name = random.choice(PAKISTANI_FIRST_NAMES_MALE) if gender == "Male" else random.choice(PAKISTANI_FIRST_NAMES_FEMALE)
        last_name = random.choice(PAKISTANI_LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        city = "Lahore" if random.random() < 0.65 else "Islamabad"
        area = random.choice(LAHORE_AREAS) if city == "Lahore" else random.choice(ISLAMABAD_AREAS)
        address = f"House {random.randint(1, 450)}, Street {random.randint(1, 35)}, {area}, {city}"

        # Assign Age Bracket
        # 10% infants/kids (<12), 65% working adults (18-50), 25% elderly (51-78)
        dice = random.random()
        if dice < 0.10:
            age = random.randint(1, 11)
        elif dice < 0.75:
            age = random.randint(18, 50)
        else:
            age = random.randint(51, 78)

        birth_date = date.today() - timedelta(days=int(age * 365.25) + random.randint(0, 300))

        # Unique CNIC & Phone
        cnic = generate_cnic(gender, city)
        while cnic in used_cnics:
            cnic = generate_cnic(gender, city)
        used_cnics.add(cnic)

        phone = generate_phone()
        while phone in used_phones:
            phone = generate_phone()
        used_phones.add(phone)

        # Match preferred branch to city
        city_branches = [b for b in branches if b.city == city]
        preferred_branch = random.choice(city_branches)

        patient = Patient(
            id=f"pat-{p_idx+1:04d}",
            cnic=cnic,
            full_name=full_name,
            gender=gender,
            date_of_birth=birth_date,
            phone=phone,
            email=f"{first_name.lower()}.{last_name.lower()}{p_idx+1}@gmail.com",
            city=city,
            address=address,
            blood_group=random.choice(["A+", "B+", "O+", "AB+", "A-", "B-", "O-"]),
            preferred_branch_id=preferred_branch.id,
            active=True
        )
        session.add(patient)
        patients.append((patient, age))

    session.commit()
    print(f"   Successfully added {len(patients)} Pakistani patients.")

    # 4. Seed Correlated Conditions, Allergies & Active Medications
    print("\n4. Seeding Correlated Conditions, Documented Allergies & Medications...")
    condition_count = 0
    med_count = 0

    for idx, (patient, age) in enumerate(patients):
        # A. INTENTIONAL ALLERGY ASSIGNMENT (Critical for Safety Agent Guardrail)
        # Ensure at least 40 patients have documented Penicillin allergy
        # Ensure 25 patients have Sulfa allergy, 20 have Aspirin/NSAID allergy
        if idx % 12 == 0 or idx in [5, 10, 25, 42, 99]:
            cond = Condition(
                patient_id=patient.id,
                category="allergy_intolerance",
                code_display="Penicillin Allergy",
                clinical_status="active",
                verification_status="confirmed",
                severity="severe_anaphylaxis",
                onset_date=date.today() - timedelta(days=random.randint(300, 3000))
            )
            session.add(cond)
            condition_count += 1

        if idx % 20 == 0:
            cond = Condition(
                patient_id=patient.id,
                category="allergy_intolerance",
                code_display="Sulfa Drugs Allergy",
                clinical_status="active",
                verification_status="confirmed",
                severity="moderate",
                onset_date=date.today() - timedelta(days=random.randint(200, 2000))
            )
            session.add(cond)
            condition_count += 1

        if idx % 25 == 0:
            cond = Condition(
                patient_id=patient.id,
                category="allergy_intolerance",
                code_display="Aspirin / NSAIDs Allergy",
                clinical_status="active",
                verification_status="confirmed",
                severity="moderate",
                onset_date=date.today() - timedelta(days=random.randint(100, 1500))
            )
            session.add(cond)
            condition_count += 1

        # B. CHRONIC CONDITIONS CORRELATED WITH AGE & MEDICATIONS
        if age > 45 and random.random() < 0.40:
            # Diabetes Mellitus
            cond = Condition(
                patient_id=patient.id,
                category="chronic_disease",
                code_display="Type 2 Diabetes Mellitus",
                clinical_status="active",
                verification_status="confirmed",
                severity="moderate",
                onset_date=date.today() - timedelta(days=random.randint(365, 3000))
            )
            session.add(cond)
            condition_count += 1

            # Correlated Medication: Glucophage or Getryl
            gluc = next(m for m in PAKISTAN_MEDICATIONS if m["brand"] == "Glucophage")
            med = MedicationRequest(
                patient_id=patient.id,
                medication_name=gluc["generic"],
                brand_name=gluc["brand"],
                dosage_instruction=gluc["dose_inst"],
                max_daily_dose_mg=gluc["max_dose"],
                status="active",
                prescribed_date=datetime.now() - timedelta(days=random.randint(10, 180))
            )
            session.add(med)
            med_count += 1

        if age > 40 and random.random() < 0.45:
            # Essential Hypertension
            cond = Condition(
                patient_id=patient.id,
                category="chronic_disease",
                code_display="Essential Hypertension",
                clinical_status="active",
                verification_status="confirmed",
                severity="moderate",
                onset_date=date.today() - timedelta(days=random.randint(365, 2500))
            )
            session.add(cond)
            condition_count += 1

            # Correlated Medication: Concor or Norvasc
            concor = next(m for m in PAKISTAN_MEDICATIONS if m["brand"] == "Concor")
            med = MedicationRequest(
                patient_id=patient.id,
                medication_name=concor["generic"],
                brand_name=concor["brand"],
                dosage_instruction=concor["dose_inst"],
                max_daily_dose_mg=concor["max_dose"],
                status="active",
                prescribed_date=datetime.now() - timedelta(days=random.randint(15, 200))
            )
            session.add(med)
            med_count += 1

        if age < 16 and random.random() < 0.25:
            # Childhood Asthma
            cond = Condition(
                patient_id=patient.id,
                category="chronic_disease",
                code_display="Bronchial Asthma",
                clinical_status="active",
                verification_status="confirmed",
                severity="moderate",
                onset_date=date.today() - timedelta(days=random.randint(100, 1000))
            )
            session.add(cond)
            condition_count += 1

            vent = next(m for m in PAKISTAN_MEDICATIONS if m["brand"] == "Ventolin Inhaler")
            med = MedicationRequest(
                patient_id=patient.id,
                medication_name=vent["generic"],
                brand_name=vent["brand"],
                dosage_instruction=vent["dose_inst"],
                max_daily_dose_mg=vent["max_dose"],
                status="active",
                prescribed_date=datetime.now() - timedelta(days=random.randint(5, 60))
            )
            session.add(med)
            med_count += 1

    session.commit()
    print(f"   Successfully added {condition_count} conditions/allergies and {med_count} active prescriptions.")

    # 5. Seed Historical Encounters & Upcoming Appointments
    print("\n5. Seeding Appointments, Visit Encounters & Queue Tokens...")
    appointment_count = 0
    token_num = 101

    for p_idx, (patient, age) in enumerate(patients):
        # Determine appropriate doctor based on age and conditions
        if age < 12:
            specialty = "Paediatrics"
        elif age > 50 and random.random() < 0.35:
            specialty = "Cardiology"
        elif random.random() < 0.50:
            specialty = "General Medicine"
        else:
            specialty = random.choice(SPECIALTIES)

        matched_docs = [d for d in practitioners if d.specialty == specialty]
        doc = random.choice(matched_docs)

        # Create 1 Past Encounter for 70% of patients
        if random.random() < 0.70:
            past_date = datetime.now() - timedelta(days=random.randint(3, 90), hours=random.randint(1, 8))
            past_appt = Appointment(
                patient_id=patient.id,
                practitioner_id=doc.id,
                branch_id=doc.primary_branch_id,
                token_number=f"CC-{token_num}",
                start_time=past_date,
                end_time=past_date + timedelta(minutes=15),
                status="fulfilled",
                appointment_type="routine",
                chief_complaint="Routine health consultation and regular follow-up.",
                urgency_tier="ROUTINE",
                clinical_notes="Patient reviewed. Vitals stable. Advised diet control and routine follow-up."
            )
            session.add(past_appt)
            token_num += 1
            appointment_count += 1

        # Create 1 Upcoming Appointment for 25% of patients
        if random.random() < 0.25:
            future_date = datetime.now() + timedelta(days=random.randint(1, 7), hours=random.randint(1, 6))
            future_appt = Appointment(
                patient_id=patient.id,
                practitioner_id=doc.id,
                branch_id=doc.primary_branch_id,
                token_number=f"CC-{token_num}",
                start_time=future_date,
                end_time=future_date + timedelta(minutes=15),
                status="booked",
                appointment_type="routine",
                chief_complaint="Follow-up consultation for symptom management.",
                urgency_tier="ROUTINE"
            )
            session.add(future_appt)
            token_num += 1
            appointment_count += 1

    session.commit()
    print(f"   Successfully added {appointment_count} appointments.")

    # 6. Seed Correlated Lab Observations (CBC, LFT, Lipid, HbA1c, Vitals)
    print("\n6. Seeding Correlated Lab Observations & Vitals...")
    obs_count = 0

    # Retrieve all fulfilled appointments
    fulfilled_appts = session.query(Appointment).filter(Appointment.status == "fulfilled").all()

    for appt in fulfilled_appts:
        # Check patient conditions
        p_conditions = [c.code_display for c in appt.patient.conditions]
        
        # Every visit gets Blood Pressure Observation
        is_hypertensive = "Essential Hypertension" in p_conditions
        sys_bp = random.randint(138, 160) if is_hypertensive else random.randint(110, 128)
        dia_bp = random.randint(88, 100) if is_hypertensive else random.randint(70, 84)

        bp_obs = Observation(
            patient_id=appt.patient_id,
            appointment_id=appt.id,
            category="vital_signs",
            code_display="Blood Pressure (Systolic/Diastolic)",
            value_quantity=float(sys_bp),
            unit="mmHg",
            reference_range="90-120 / 60-80",
            interpretation="high" if is_hypertensive else "normal",
            issued_date=appt.start_time
        )
        session.add(bp_obs)
        obs_count += 1

        # If Diabetic, add HbA1c
        if "Type 2 Diabetes Mellitus" in p_conditions:
            hba1c_val = round(random.uniform(7.1, 9.8), 1)
            hba1c_obs = Observation(
                patient_id=appt.patient_id,
                appointment_id=appt.id,
                category="laboratory",
                code_display="HbA1c (Glycated Hemoglobin)",
                value_quantity=hba1c_val,
                unit="%",
                reference_range="4.0 - 5.6",
                interpretation="high" if hba1c_val > 6.5 else "normal",
                issued_date=appt.start_time
            )
            session.add(hba1c_obs)
            obs_count += 1

        # CBC Observations for 40% of visits (Platelets & Haemoglobin)
        if random.random() < 0.40:
            # Platelets
            # Occasionally low for testing (Dengue/Thrombocytopenia scenario)
            low_platelet = (random.random() < 0.15)
            plat_val = random.randint(75000, 130000) if low_platelet else random.randint(160000, 380000)
            
            plat_obs = Observation(
                patient_id=appt.patient_id,
                appointment_id=appt.id,
                category="laboratory",
                code_display="Platelet Count",
                value_quantity=float(plat_val),
                unit="/mcL",
                reference_range="150,000 - 450,000",
                interpretation="low" if plat_val < 150000 else "normal",
                issued_date=appt.start_time
            )
            session.add(plat_obs)
            obs_count += 1

            # Haemoglobin
            is_anemic = (appt.patient.gender == "Female" and random.random() < 0.35)
            hb_val = round(random.uniform(8.5, 11.2) if is_anemic else random.uniform(12.5, 16.0), 1)
            hb_obs = Observation(
                patient_id=appt.patient_id,
                appointment_id=appt.id,
                category="laboratory",
                code_display="Haemoglobin (Hb)",
                value_quantity=hb_val,
                unit="g/dL",
                reference_range="12.0 - 15.5",
                interpretation="low" if hb_val < 12.0 else "normal",
                issued_date=appt.start_time
            )
            session.add(hb_obs)
            obs_count += 1

    session.commit()
    print(f"   Successfully added {obs_count} clinical lab observations.")

    # 7. Add Baseline Audit Log
    audit = AuditLog(
        user_id="SYSTEM_ADMIN",
        user_role="ADMIN",
        action_type="DATABASE_SEEDED",
        resource_type="ALL_TABLES",
        resource_id="ALL",
        details="Initial synthetic data loaded: 5 branches, 30 doctors, 500 patients, conditions, prescriptions, and labs.",
        is_emergency=False
    )
    session.add(audit)
    session.commit()

    print("\n" + "=" * 70)
    print("[SUCCESS] DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"Summary of Records Created:")
    print(f"- Clinic Branches:        {len(branches)}")
    print(f"- Doctors:                {len(practitioners)} across 6 specialties")
    print(f"- Patients:               {len(patients)} (Pakistani demographics)")
    print(f"- Conditions & Allergies: {condition_count}")
    print(f"- Active Prescriptions:   {med_count}")
    print(f"- Appointments:           {appointment_count}")
    print(f"- Clinical Observations:  {obs_count}")
    print("=" * 70)

    session.close()

if __name__ == "__main__":
    seed_database()
