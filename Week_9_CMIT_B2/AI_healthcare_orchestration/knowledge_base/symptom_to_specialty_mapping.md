# City Care Clinics - Clinical Symptom-to-Specialty Mapping Protocol

This document establishes the clinical routing logic and symptom keyword dictionaries used by the **Scheduling Agent** and **Supervisor Agent** to correctly match patient presentations to the 6 clinic specialties.

---

## 1. Golden Age & Emergency 1122 Overrides (Seene mein shadeed dard aur thanda paseena)
1. **Paediatric Absolute Rule (8 saal ka bacha ya 14 saal se chota):** Any patient aged **under 14 years** presenting with non-emergent medical complaints (like ulti, dast, bukhar) MUST be booked with a **Paediatrician / Paediatrics specialist** (Dr. Fatima Zahra, Dr. Usman Ghani, Dr. Maryam Noor, Dr. Hamza Ali, Dr. Sadia Bashir).
2. **Emergency Red-Flag Override (Seene mein dard aur paseena):** Any presentation featuring sudden crushing chest pain, diaphoresis (thanda paseena), stroke symptoms (FAST), acute respiratory failure, or massive hemorrhage bypasses outpatient specialty booking and immediately triggers the **Rescue 1122 Emergency Protocol**. The patient must be transferred to the nearest emergency hospital immediately.

---

## 2. Clinical Specialty Profiles & Symptom Guidelines

### General Medicine (Internal Medicine)
- **Primary Clinical Scope:** Adult systemic infections, fever workup, metabolic disorders, diabetes management, unexplained weight loss, fatigue, digestive issues, joints pain.
- **Common Symptoms:** Fever > 3 days, body aches, persistent cough, unexplained fatigue, jaundice, diarrhea/vomiting in adults, uncontrolled blood sugar, high uric acid.
- **UrduLish Triggers:** *"Bukhar"*, *"Khansi"*, *"Gala kharab"*, *"Jism mein dard"*, *"Thakan"*, *"Pet kharab"*, *"Sugar barh gayi"*, *"Dast"*, *"Ultee"* (adults).

### Paediatrics (8 saal ka bacha / Chota bacha / Ulti aur Dast)
- **Primary Clinical Scope:** All illnesses, vaccinations, developmental assessments, growth monitoring, and nutritional advice for patients under 14 years (8 saal ka bacha ya nawzaida).
- **Common Symptoms:** Child with fever, rash in toddler, poor feeding in infant, persistent vomiting/diarrhea in child (ulti aur dast), recurrent wheeze, routine EPI vaccine inquiry.
- **UrduLish Triggers:** *"Bacha"*, *"Chota bacha"*, *"8 saal ka bacha"*, *"Betay ko bukhar"*, *"Beti ki ultiyan"*, *"Bachay ko ulti aur dast"*, *"Doodh nahi pee raha"*, *"Tika lagwana"* (vaccination), *"Bachay ka wazan"*.

### Gynaecology & Obstetrics (Women's Health)
- **Primary Clinical Scope:** Women's reproductive health, prenatal/antenatal checkups, menstrual irregularities, fertility concerns, pelvic pain, menopause.
- **Common Symptoms:** Missed periods, pregnancy confirmation, irregular bleeding, severe dysmenorrhea, white discharge, pelvic heaviness, PCOS symptoms.
- **UrduLish Triggers:** *"Mahwari"*, *"Periods irregular"*, *"Hamal / Pregnancy"* checkup, *"Pait ke nichle hissay mein dard"*, *"Likoria / White discharge"*, *"Ultrasound scan"* (pregnancy).

### Cardiology (Heart & Vascular Care)
- **Primary Clinical Scope:** Cardiovascular disorders, hypertension, palpitations, exertional shortness of breath, lipid management, post-stent/bypass follow-up.
- **Common Symptoms:** High blood pressure readings, heart racing/palpitations, breathlessness on climbing stairs, swollen ankles (edema), chronic stable angina.
- **UrduLish Triggers:** *"Blood pressure barh gaya"*, *"Dil ki dharkan tez"*, *"Dil ghabrana"*, *"Seeriyan charhte waqt saans phoolna"*, *"Paon par sujan"*, *"Cholesterol issue"*.

### Dermatology (Skin, Hair & Nails)
- **Primary Clinical Scope:** Skin diseases, hair loss, nail disorders, chronic eczema, psoriasis, acne vulgaris, cosmetic dermatology, fungal rashes.
- **Common Symptoms:** Pimples, cystic acne, severe hair fall, baldness, itchy red patches on skin, ringworm, fungal groin rash, dark spots (melasma), dry peeling skin.
- **UrduLish Triggers:** *"Skin par daanay"*, *"Keel mohasay / Acne"*, *"Baal girna / Hair fall"*, *"Kharish"*, *"Chambal / Daad / Fungus"*, *"Chehray par jhaiyan"*, *"Surkh nishan"*.

### ENT (Ear, Nose & Throat)
- **Primary Clinical Scope:** Diseases of ear, auditory canal, nasal sinuses, oral cavity, pharynx, tonsils, larynx, balance and vertigo disorders.
- **Common Symptoms:** Ear discharge, severe earache, ringing in ears (tinnitus), blocked nasal passages, chronic sinusitis, hoarseness of voice, difficulty swallowing, dizziness/vertigo.
- **UrduLish Triggers:** *"Kaan mein dard"*, *"Kaan se peep aana"*, *"Naak band"*, *"Sinus ka masla"*, *"Chakkar aana"*, *"Gala pak gaya / Tonsils"*, *"Aawaz baith jana"*, *"Sunai kam dena"*.

---

## 3. Ambiguous & Cross-Specialty Routing Protocols
- **Chest Discomfort vs. Heartburn (Acid Reflux):**
  - If burning occurs after spicy meals, is relieved by antacids (e.g. Risek, Gaviscon), and has no exertion link $\rightarrow$ Route to **General Medicine**.
  - If discomfort is triggered by walking, radiates to jaw/arm, or is accompanied by breathlessness $\rightarrow$ Immediate Cardiology evaluation or Emergency screening.
- **Shortness of Breath:**
  - With wheezing and cough in known asthmatic $\rightarrow$ **General Medicine** (or **Paediatrics** if <14).
  - With ankle swelling and history of high BP $\rightarrow$ **Cardiology**.
- **Child with Earache:**
  - Standard child earache / middle ear infection $\rightarrow$ **Paediatrics** first; escalate to **ENT** if chronic perforation or failed response.
