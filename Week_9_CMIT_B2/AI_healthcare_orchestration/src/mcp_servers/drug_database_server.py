"""
MCP Server: drug-database
Provides clinical pharmacology and drug safety services:
- lookup_drug: Detailed lookup of 100 common Pakistani brand and generic medicines
- check_drug_interactions: Pairwise clinical drug-drug interaction screening
- check_max_dose: Dose threshold verification against maximum safe daily limits
- check_allergy_contraindication: Cross-checks proposed drug against patient allergies
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.mcpserver import MCPServer

server = MCPServer("drug-database")

# Comprehensive Pakistani Formulary (100 Core Drugs)
PAKISTANI_FORMULARY = [
    # Analgesics & Antipyretics
    {"brand": "Panadol", "generic": "Paracetamol", "dose_inst": "500mg every 6 hours as needed", "max_dose_mg": 4000, "class": "Analgesic", "route": "Oral"},
    {"brand": "Panadol Extra", "generic": "Paracetamol + Caffeine", "dose_inst": "500/65mg every 8 hours", "max_dose_mg": 4000, "class": "Analgesic", "route": "Oral"},
    {"brand": "Calpol Syrup", "generic": "Paracetamol", "dose_inst": "120mg/5ml, 5ml three times daily", "max_dose_mg": 2000, "class": "Analgesic", "route": "Oral"},
    {"brand": "Disprin", "generic": "Aspirin (Acetylsalicylic Acid)", "dose_inst": "300mg dissolved in water", "max_dose_mg": 3000, "class": "NSAID", "route": "Oral"},
    {"brand": "Loprin", "generic": "Low-dose Aspirin", "dose_inst": "75mg once daily after lunch", "max_dose_mg": 150, "class": "Antiplatelet", "route": "Oral"},
    {"brand": "Brufen", "generic": "Ibuprofen", "dose_inst": "400mg twice daily after meals", "max_dose_mg": 2400, "class": "NSAID", "route": "Oral"},
    {"brand": "Arinac", "generic": "Ibuprofen + Pseudoephedrine", "dose_inst": "1 tablet twice daily", "max_dose_mg": 1200, "class": "Decongestant/NSAID", "route": "Oral"},
    {"brand": "Ponstan", "generic": "Mefenamic Acid", "dose_inst": "500mg three times daily after meals", "max_dose_mg": 1500, "class": "NSAID", "route": "Oral"},
    {"brand": "Voltral", "generic": "Diclofenac Sodium", "dose_inst": "50mg twice daily after meals", "max_dose_mg": 150, "class": "NSAID", "route": "Oral"},
    {"brand": "Ansaid", "generic": "Flurbiprofen", "dose_inst": "100mg twice daily", "max_dose_mg": 300, "class": "NSAID", "route": "Oral"},
    {"brand": "Toradol", "generic": "Ketorolac Tromethamine", "dose_inst": "10mg every 6 hours for max 5 days", "max_dose_mg": 40, "class": "NSAID", "route": "Oral"},
    {"brand": "Celebrex", "generic": "Celecoxib", "dose_inst": "200mg once daily", "max_dose_mg": 400, "class": "COX-2 Inhibitor", "route": "Oral"},
    {"brand": "Synflex", "generic": "Naproxen Sodium", "dose_inst": "550mg twice daily", "max_dose_mg": 1100, "class": "NSAID", "route": "Oral"},
    {"brand": "Tramal", "generic": "Tramadol HCl", "dose_inst": "50mg twice daily as needed", "max_dose_mg": 400, "class": "Opioid Analgesic", "route": "Oral"},

    # Antibiotics & Anti-infectives
    {"brand": "Augmentin", "generic": "Amoxicillin + Clavulanic Acid", "dose_inst": "625mg twice daily for 7 days", "max_dose_mg": 2000, "class": "Penicillin Antibiotic", "route": "Oral"},
    {"brand": "Augmentin 1g", "generic": "Amoxicillin + Clavulanic Acid", "dose_inst": "1000mg twice daily for 7 days", "max_dose_mg": 2000, "class": "Penicillin Antibiotic", "route": "Oral"},
    {"brand": "Amoxil", "generic": "Amoxicillin", "dose_inst": "500mg three times daily", "max_dose_mg": 3000, "class": "Penicillin Antibiotic", "route": "Oral"},
    {"brand": "Ampiclox", "generic": "Ampicillin + Cloxacillin", "dose_inst": "500mg four times daily", "max_dose_mg": 4000, "class": "Penicillin Antibiotic", "route": "Oral"},
    {"brand": "Cravit", "generic": "Levofloxacin", "dose_inst": "500mg once daily for 7 days", "max_dose_mg": 750, "class": "Fluoroquinolone", "route": "Oral"},
    {"brand": "Ciprobid", "generic": "Ciprofloxacin", "dose_inst": "500mg twice daily for 5 days", "max_dose_mg": 1500, "class": "Fluoroquinolone", "route": "Oral"},
    {"brand": "Avelox", "generic": "Moxifloxacin", "dose_inst": "400mg once daily", "max_dose_mg": 400, "class": "Fluoroquinolone", "route": "Oral"},
    {"brand": "Klaricid", "generic": "Clarithromycin", "dose_inst": "500mg twice daily for 10 days", "max_dose_mg": 1000, "class": "Macrolide", "route": "Oral"},
    {"brand": "Azomax", "generic": "Azithromycin", "dose_inst": "500mg once daily for 3 days", "max_dose_mg": 500, "class": "Macrolide", "route": "Oral"},
    {"brand": "Zithrokan", "generic": "Azithromycin", "dose_inst": "250mg once daily", "max_dose_mg": 500, "class": "Macrolide", "route": "Oral"},
    {"brand": "Cefspan", "generic": "Cefixime", "dose_inst": "400mg once daily for 5 days", "max_dose_mg": 800, "class": "Cephalosporin", "route": "Oral"},
    {"brand": "Rocephin", "generic": "Ceftriaxone", "dose_inst": "1g IM/IV once daily", "max_dose_mg": 2000, "class": "Cephalosporin", "route": "Injectable"},
    {"brand": "Velosef", "generic": "Cephradine", "dose_inst": "500mg four times daily", "max_dose_mg": 4000, "class": "Cephalosporin", "route": "Oral"},
    {"brand": "Ceporex", "generic": "Cephalexin", "dose_inst": "500mg every 6 hours", "max_dose_mg": 4000, "class": "Cephalosporin", "route": "Oral"},
    {"brand": "Flagyl", "generic": "Metronidazole", "dose_inst": "400mg three times daily for 5 days", "max_dose_mg": 1500, "class": "Nitroimidazole", "route": "Oral"},
    {"brand": "Entamizole", "generic": "Metronidazole + Diloxanide Furoate", "dose_inst": "1 tablet three times daily", "max_dose_mg": 1500, "class": "Antiamoebic", "route": "Oral"},
    {"brand": "Septran", "generic": "Co-trimoxazole (Sulfamethoxazole + Trimethoprim)", "dose_inst": "960mg twice daily", "max_dose_mg": 1920, "class": "Sulfonamide Antibiotic", "route": "Oral"},
    {"brand": "Vibramycin", "generic": "Doxycycline", "dose_inst": "100mg once daily after meal", "max_dose_mg": 200, "class": "Tetracycline", "route": "Oral"},
    {"brand": "Fucidin", "generic": "Fusidic Acid", "dose_inst": "Apply cream twice daily topically", "max_dose_mg": 0, "class": "Topical Antibacterial", "route": "Topical"},

    # Gastrointestinal & Acid Reducers
    {"brand": "Risek", "generic": "Omeprazole", "dose_inst": "20mg once daily before breakfast", "max_dose_mg": 40, "class": "PPI", "route": "Oral"},
    {"brand": "Risek Insta", "generic": "Omeprazole + Sodium Bicarbonate", "dose_inst": "20mg sachet once daily", "max_dose_mg": 40, "class": "PPI", "route": "Oral"},
    {"brand": "Nexum", "generic": "Esomeprazole", "dose_inst": "40mg once daily before breakfast", "max_dose_mg": 80, "class": "PPI", "route": "Oral"},
    {"brand": "Zopent", "generic": "Pantoprazole", "dose_inst": "40mg once daily before meals", "max_dose_mg": 80, "class": "PPI", "route": "Oral"},
    {"brand": "Getzome", "generic": "Omeprazole", "dose_inst": "40mg once daily", "max_dose_mg": 40, "class": "PPI", "route": "Oral"},
    {"brand": "Gravinate", "generic": "Dimenhydrinate", "dose_inst": "50mg as needed for nausea", "max_dose_mg": 300, "class": "Antiemetic", "route": "Oral"},
    {"brand": "Motilium", "generic": "Domperidone", "dose_inst": "10mg three times daily before meals", "max_dose_mg": 30, "class": "Prokinetic", "route": "Oral"},
    {"brand": "Maxolon", "generic": "Metoclopramide", "dose_inst": "10mg three times daily", "max_dose_mg": 30, "class": "Antiemetic", "route": "Oral"},
    {"brand": "Gaviscon Liquid", "generic": "Sodium Alginate + Potassium Bicarbonate", "dose_inst": "10ml after meals and at bedtime", "max_dose_mg": 4000, "class": "Antacid", "route": "Oral"},
    {"brand": "Mucaine", "generic": "Oxethazaine + Antacids", "dose_inst": "10ml 15 min before meals", "max_dose_mg": 40, "class": "Antacid/Anesthetic", "route": "Oral"},
    {"brand": "Spasfon", "generic": "Phloroglucinol", "dose_inst": "1 tablet as needed for cramps", "max_dose_mg": 600, "class": "Antispasmodic", "route": "Oral"},
    {"brand": "Buscopan", "generic": "Hyoscine Butylbromide", "dose_inst": "10mg three times daily for spasms", "max_dose_mg": 60, "class": "Antispasmodic", "route": "Oral"},
    {"brand": "Colofac", "generic": "Mebeverine HCl", "dose_inst": "135mg three times daily before meals", "max_dose_mg": 405, "class": "Antispasmodic", "route": "Oral"},
    {"brand": "Duphalac", "generic": "Lactulose", "dose_inst": "15ml twice daily", "max_dose_mg": 60, "class": "Laxative", "route": "Oral"},
    {"brand": "Imodium", "generic": "Loperamide", "dose_inst": "2mg after each loose stool", "max_dose_mg": 16, "class": "Antidiarrheal", "route": "Oral"},

    # Cardiovascular & Antihypertensives
    {"brand": "Concor", "generic": "Bisoprolol Fumarate", "dose_inst": "5mg once daily in morning", "max_dose_mg": 10, "class": "Beta Blocker", "route": "Oral"},
    {"brand": "Concor Cor", "generic": "Bisoprolol Fumarate", "dose_inst": "2.5mg once daily", "max_dose_mg": 10, "class": "Beta Blocker", "route": "Oral"},
    {"brand": "Inderal", "generic": "Propranolol HCl", "dose_inst": "10mg twice daily", "max_dose_mg": 160, "class": "Beta Blocker", "route": "Oral"},
    {"brand": "Norvasc", "generic": "Amlodipine Besylate", "dose_inst": "5mg once daily", "max_dose_mg": 10, "class": "Calcium Channel Blocker", "route": "Oral"},
    {"brand": "Softvasc", "generic": "Amlodipine", "dose_inst": "10mg once daily", "max_dose_mg": 10, "class": "Calcium Channel Blocker", "route": "Oral"},
    {"brand": "Capoten", "generic": "Captopril", "dose_inst": "25mg twice daily", "max_dose_mg": 150, "class": "ACE Inhibitor", "route": "Oral"},
    {"brand": "Zestril", "generic": "Lisinopril", "dose_inst": "10mg once daily", "max_dose_mg": 40, "class": "ACE Inhibitor", "route": "Oral"},
    {"brand": "Cozaar", "generic": "Losartan Potassium", "dose_inst": "50mg once daily", "max_dose_mg": 100, "class": "ARB", "route": "Oral"},
    {"brand": "Hyzaar", "generic": "Losartan + Hydrochlorothiazide", "dose_inst": "50/12.5mg once daily", "max_dose_mg": 100, "class": "ARB/Diuretic", "route": "Oral"},
    {"brand": "Diovan", "generic": "Valsartan", "dose_inst": "80mg once daily", "max_dose_mg": 320, "class": "ARB", "route": "Oral"},
    {"brand": "Exforge", "generic": "Amlodipine + Valsartan", "dose_inst": "5/80mg once daily", "max_dose_mg": 10, "class": "CCB/ARB", "route": "Oral"},
    {"brand": "Lasix", "generic": "Furosemide", "dose_inst": "40mg once daily morning", "max_dose_mg": 80, "class": "Loop Diuretic", "route": "Oral"},
    {"brand": "Spiromide", "generic": "Spironolactone + Furosemide", "dose_inst": "50/20mg once daily", "max_dose_mg": 100, "class": "Diuretic Combo", "route": "Oral"},
    {"brand": "Aldactone", "generic": "Spironolactone", "dose_inst": "25mg once daily", "max_dose_mg": 100, "class": "Potassium-sparing Diuretic", "route": "Oral"},
    {"brand": "Lipitor", "generic": "Atorvastatin Calcium", "dose_inst": "20mg at bedtime", "max_dose_mg": 80, "class": "Statin", "route": "Oral"},
    {"brand": "Atorva", "generic": "Atorvastatin", "dose_inst": "10mg at bedtime", "max_dose_mg": 80, "class": "Statin", "route": "Oral"},
    {"brand": "Crestor", "generic": "Rosuvastatin Calcium", "dose_inst": "10mg at bedtime", "max_dose_mg": 40, "class": "Statin", "route": "Oral"},
    {"brand": "Roseday", "generic": "Rosuvastatin", "dose_inst": "5mg at bedtime", "max_dose_mg": 40, "class": "Statin", "route": "Oral"},
    {"brand": "Plavix", "generic": "Clopidogrel", "dose_inst": "75mg once daily", "max_dose_mg": 75, "class": "Antiplatelet", "route": "Oral"},
    {"brand": "Angised", "generic": "Glyceryl Trinitrate (GTN)", "dose_inst": "0.5mg sublingual as needed for angina", "max_dose_mg": 3, "class": "Nitrate", "route": "Sublingual"},

    # Diabetes & Endocrine
    {"brand": "Glucophage", "generic": "Metformin HCl", "dose_inst": "500mg twice daily with meals", "max_dose_mg": 2000, "class": "Biguanide", "route": "Oral"},
    {"brand": "Glucophage XR", "generic": "Metformin Extended Release", "dose_inst": "1000mg once daily with dinner", "max_dose_mg": 2000, "class": "Biguanide", "route": "Oral"},
    {"brand": "Getryl", "generic": "Glimepiride", "dose_inst": "2mg once daily before breakfast", "max_dose_mg": 8, "class": "Sulfonylurea", "route": "Oral"},
    {"brand": "Amaryl", "generic": "Glimepiride", "dose_inst": "1mg once daily", "max_dose_mg": 8, "class": "Sulfonylurea", "route": "Oral"},
    {"brand": "Diamicron MR", "generic": "Gliclazide Modified Release", "dose_inst": "60mg with breakfast", "max_dose_mg": 120, "class": "Sulfonylurea", "route": "Oral"},
    {"brand": "Januvia", "generic": "Sitagliptin", "dose_inst": "100mg once daily", "max_dose_mg": 100, "class": "DPP-4 Inhibitor", "route": "Oral"},
    {"brand": "Janumet", "generic": "Sitagliptin + Metformin", "dose_inst": "50/500mg twice daily", "max_dose_mg": 2000, "class": "DPP-4/Biguanide", "route": "Oral"},
    {"brand": "Galvus Met", "generic": "Vildagliptin + Metformin", "dose_inst": "50/850mg twice daily", "max_dose_mg": 2000, "class": "DPP-4/Biguanide", "route": "Oral"},
    {"brand": "Jardiance", "generic": "Empagliflozin", "dose_inst": "10mg once daily morning", "max_dose_mg": 25, "class": "SGLT2 Inhibitor", "route": "Oral"},
    {"brand": "Thyroxine", "generic": "Levothyroxine Sodium", "dose_inst": "50mcg once daily empty stomach", "max_dose_mg": 200, "class": "Thyroid Hormone", "route": "Oral"},

    # Respiratory & Allergy
    {"brand": "Softin", "generic": "Loratadine", "dose_inst": "10mg once daily at night", "max_dose_mg": 10, "class": "Antihistamine", "route": "Oral"},
    {"brand": "Telfast", "generic": "Fexofenadine HCl", "dose_inst": "120mg once daily", "max_dose_mg": 180, "class": "Antihistamine", "route": "Oral"},
    {"brand": "Zyrtec", "generic": "Cetirizine HCl", "dose_inst": "10mg once daily", "max_dose_mg": 10, "class": "Antihistamine", "route": "Oral"},
    {"brand": "Rigix", "generic": "Cetirizine", "dose_inst": "10mg at bedtime", "max_dose_mg": 10, "class": "Antihistamine", "route": "Oral"},
    {"brand": "Kestine", "generic": "Ebastine", "dose_inst": "10mg once daily", "max_dose_mg": 20, "class": "Antihistamine", "route": "Oral"},
    {"brand": "Ventolin Inhaler", "generic": "Salbutamol", "dose_inst": "2 puffs as needed for wheezing", "max_dose_mg": 8, "class": "Short-acting Beta Agonist", "route": "Inhalation"},
    {"brand": "Seretide Evohaler", "generic": "Salmeterol + Fluticasone", "dose_inst": "2 puffs twice daily", "max_dose_mg": 4, "class": "ICS/LABA", "route": "Inhalation"},
    {"brand": "Symbicort Turbuhaler", "generic": "Budesonide + Formoterol", "dose_inst": "160/4.5mcg twice daily", "max_dose_mg": 4, "class": "ICS/LABA", "route": "Inhalation"},
    {"brand": "Myteka", "generic": "Montelukast Sodium", "dose_inst": "10mg at night", "max_dose_mg": 10, "class": "Leukotriene Receptor Antagonist", "route": "Oral"},
    {"brand": "Montec", "generic": "Montelukast", "dose_inst": "10mg once daily", "max_dose_mg": 10, "class": "Leukotriene Receptor Antagonist", "route": "Oral"},
    {"brand": "Hydryllin Syrup", "generic": "Aminophylline + Diphenhydramine", "dose_inst": "10ml three times daily for cough", "max_dose_mg": 30, "class": "Cough Expectorant", "route": "Oral"},
    {"brand": "Pulmonol Syrup", "generic": "Dextromethorphan + Chlorpheniramine", "dose_inst": "10ml twice daily", "max_dose_mg": 30, "class": "Cough Suppressant", "route": "Oral"},

    # Dermatology & Topical
    {"brand": "Dermovate", "generic": "Clobetasol Propionate", "dose_inst": "Apply thin layer once daily", "max_dose_mg": 0, "class": "Potent Corticosteroid", "route": "Topical"},
    {"brand": "Hydrozole Cream", "generic": "Hydrocortisone + Clotrimazole", "dose_inst": "Apply twice daily for 7 days", "max_dose_mg": 0, "class": "Antifungal/Steroid", "route": "Topical"},
    {"brand": "Travocort", "generic": "Isoconazole + Diflucortolone", "dose_inst": "Apply twice daily", "max_dose_mg": 0, "class": "Antifungal/Steroid", "route": "Topical"},
    {"brand": "Betnovate", "generic": "Betamethasone Valerate", "dose_inst": "Apply thin film twice daily", "max_dose_mg": 0, "class": "Topical Corticosteroid", "route": "Topical"},
    {"brand": "Polyfax Ointment", "generic": "Polymyxin B + Bacitracin", "dose_inst": "Apply twice daily to cuts/burns", "max_dose_mg": 0, "class": "Topical Antibiotic", "route": "Topical"},
    {"brand": "Skinoren Cream", "generic": "Azelaic Acid", "dose_inst": "Apply twice daily for acne", "max_dose_mg": 0, "class": "Acne Agent", "route": "Topical"},
    {"brand": "Canesten Cream", "generic": "Clotrimazole", "dose_inst": "Apply two to three times daily", "max_dose_mg": 0, "class": "Antifungal", "route": "Topical"},

    # ENT Specific
    {"brand": "Otrivin Nasal Drops", "generic": "Xylometazoline HCl", "dose_inst": "2 drops in each nostril max 5 days", "max_dose_mg": 3, "class": "Nasal Decongestant", "route": "Nasal"},
    {"brand": "Nasonex Nasal Spray", "generic": "Mometasone Furoate", "dose_inst": "2 sprays in each nostril daily", "max_dose_mg": 2, "class": "Nasal Corticosteroid", "route": "Nasal"},
    {"brand": "Beclodual", "generic": "Beclomethasone Dipropionate", "dose_inst": "1 spray each nostril twice daily", "max_dose_mg": 4, "class": "Nasal Corticosteroid", "route": "Nasal"},
    {"brand": "Waxsol Ear Drops", "generic": "Docusate Sodium", "dose_inst": "Fill ear at bedtime for 2 consecutive nights", "max_dose_mg": 0, "class": "Ceruminolytic", "route": "Otic"}
]

# Clinical Drug-Drug Interaction Rules (Key Clinical Pairs)
INTERACTION_RULES = [
    {
        "drugs_a": ["aspirin", "disprin", "loprin", "brufen", "ibuprofen", "voltral", "diclofenac", "ponstan", "mefenamic", "synflex", "naproxen", "ansaid"],
        "drugs_b": ["plavix", "clopidogrel", "warfarin"],
        "severity": "CRITICAL",
        "description": "High risk of gastrointestinal bleeding and hemorrhage due to combined antiplatelet/anticoagulant effects."
    },
    {
        "drugs_a": ["aspirin", "disprin", "loprin", "brufen", "ibuprofen", "voltral", "diclofenac", "ponstan"],
        "drugs_b": ["aspirin", "disprin", "brufen", "ibuprofen", "voltral", "diclofenac", "ponstan", "synflex"],
        "severity": "MODERATE",
        "description": "Concurrent use of multiple NSAIDs increases risk of peptic ulceration, GI bleeding, and nephrotoxicity without additional analgesic benefit."
    },
    {
        "drugs_a": ["capoten", "captopril", "zestril", "lisinopril", "cozaar", "losartan", "diovan", "valsartan", "hyzaar"],
        "drugs_b": ["aldactone", "spironolactone", "spiromide"],
        "severity": "HIGH",
        "description": "Risk of severe hyperkalemia and cardiac arrhythmias due to combined potassium retention."
    },
    {
        "drugs_a": ["lipitor", "atorvastatin", "atorva", "crestor", "rosuvastatin", "roseday"],
        "drugs_b": ["klaricid", "clarithromycin"],
        "severity": "HIGH",
        "description": "Clarithromycin strongly inhibits CYP3A4, significantly increasing statin serum concentrations and risk of rhabdomyolysis and myopathy."
    },
    {
        "drugs_a": ["cravit", "levofloxacin", "ciprobid", "ciprofloxacin", "avelox", "moxifloxacin"],
        "drugs_b": ["gaviscon", "mucaine", "antacid", "calcium", "magnesium", "aluminum"],
        "severity": "MODERATE",
        "description": "Chelation interaction: Polyvalent cations in antacids bind fluoroquinolones in the GI tract, severely reducing antibiotic absorption."
    },
    {
        "drugs_a": ["concor", "bisoprolol", "inderal", "propranolol"],
        "drugs_b": ["norvasc", "softvasc", "amlodipine", "verapamil", "diltiazem"],
        "severity": "MODERATE",
        "description": "Additive negative chronotropic and inotropic effects; monitor closely for severe bradycardia and hypotension."
    },
    {
        "drugs_a": ["cravit", "levofloxacin", "avelox", "moxifloxacin"],
        "drugs_b": ["klaricid", "clarithromycin", "azomax", "zithrokan", "azithromycin"],
        "severity": "HIGH",
        "description": "Additive QT interval prolongation risk, predisposing to polymorphic ventricular arrhythmias (Torsades de Pointes)."
    },
    {
        "drugs_a": ["tramal", "tramadol"],
        "drugs_b": ["hydryllin", "pulmonol", "chlorpheniramine", "diphenhydramine"],
        "severity": "HIGH",
        "description": "Synergistic CNS and respiratory depression risk; may cause severe somnolence and respiratory compromise."
    },
    {
        "drugs_a": ["glucophage", "metformin", "janumet", "galvus met"],
        "drugs_b": ["lasix", "furosemide"],
        "severity": "MODERATE",
        "description": "Loop diuretics can induce dehydration and prerenal azotemia, increasing the risk of metformin-associated lactic acidosis."
    }
]


@server.tool()
def lookup_drug(query: str) -> Dict[str, Any]:
    """
    Looks up medicine details by Pakistani brand name or generic scientific name.
    Examples: 'Augmentin', 'Panadol', 'Metformin', 'Concor', 'Risek'.
    """
    q = query.strip().lower()
    matches = []

    for drug in PAKISTANI_FORMULARY:
        if q in drug["brand"].lower() or q in drug["generic"].lower():
            matches.append(drug)

    if not matches:
        return {
            "status": "not_found",
            "query": query,
            "message": f"No formulary matches found for '{query}'. Please check spelling or consult clinical pharmacopoeia."
        }

    return {
        "status": "success",
        "query": query,
        "match_count": len(matches),
        "results": matches
    }


@server.tool()
def check_drug_interactions(drugs: List[str]) -> Dict[str, Any]:
    """
    Evaluates potential drug-drug interactions for a proposed combination of medications.
    Pass a list of brand or generic drug names (e.g. ['Loprin', 'Voltral', 'Klaricid']).
    """
    if len(drugs) < 2:
        return {
            "status": "success",
            "has_interactions": False,
            "interactions_count": 0,
            "interactions": [],
            "message": "At least two drugs are required to evaluate drug-drug interactions."
        }

    cleaned_drugs = [d.strip().lower() for d in drugs if d.strip()]
    found_interactions = []

    # Pairwise comparison against interaction rules
    for i in range(len(cleaned_drugs)):
        for j in range(i + 1, len(cleaned_drugs)):
            d1 = cleaned_drugs[i]
            d2 = cleaned_drugs[j]

            for rule in INTERACTION_RULES:
                match_1a = any(k in d1 for k in rule["drugs_a"])
                match_2b = any(k in d2 for k in rule["drugs_b"])

                match_1b = any(k in d1 for k in rule["drugs_b"])
                match_2a = any(k in d2 for k in rule["drugs_a"])

                if (match_1a and match_2b) or (match_1b and match_2a):
                    # Prevent duplicates
                    interaction_entry = {
                        "drug_1": drugs[i],
                        "drug_2": drugs[j],
                        "severity": rule["severity"],
                        "clinical_effect": rule["description"]
                    }
                    if interaction_entry not in found_interactions:
                        found_interactions.append(interaction_entry)

    return {
        "status": "success",
        "analyzed_drugs": drugs,
        "has_interactions": len(found_interactions) > 0,
        "interactions_count": len(found_interactions),
        "interactions": found_interactions,
        "recommendation": "Review high/critical interactions before issuing prescription." if found_interactions else "No clinically significant drug interactions detected in formulary database."
    }


@server.tool()
def check_max_dose(drug_name: str, proposed_daily_dose_mg: float) -> Dict[str, Any]:
    """
    Validates a proposed total daily dosage (in mg) against standard maximum safe daily thresholds.
    """
    q = drug_name.strip().lower()
    matched_drug = None

    for drug in PAKISTANI_FORMULARY:
        if q in drug["brand"].lower() or q in drug["generic"].lower():
            matched_drug = drug
            break

    if not matched_drug:
        return {
            "status": "not_found",
            "drug_name": drug_name,
            "message": f"Dosage threshold for '{drug_name}' not available in local formulary."
        }

    max_dose = matched_drug["max_dose_mg"]
    if max_dose == 0:
        return {
            "status": "success",
            "drug": matched_drug["brand"],
            "generic": matched_drug["generic"],
            "note": "Topical or Otic/Nasal preparation. Daily mg threshold does not apply; follow application guidelines.",
            "standard_instruction": matched_drug["dose_inst"]
        }

    exceeds = proposed_daily_dose_mg > max_dose
    pct = round((proposed_daily_dose_mg / max_dose) * 100, 1)

    return {
        "status": "success",
        "drug": matched_drug["brand"],
        "generic": matched_drug["generic"],
        "proposed_daily_dose_mg": proposed_daily_dose_mg,
        "maximum_safe_daily_dose_mg": max_dose,
        "percentage_of_max_dose": f"{pct}%",
        "is_safe": not exceeds,
        "alert": f"OVERDOSE WARNING: Proposed dose {proposed_daily_dose_mg}mg exceeds max safe limit of {max_dose}mg/day." if exceeds else "Dosage is within safe clinical limits.",
        "standard_instruction": matched_drug["dose_inst"]
    }


@server.tool()
def check_allergy_contraindication(drug_name: str, patient_allergies: List[str]) -> Dict[str, Any]:
    """
    Screens proposed drug against known patient allergies (e.g. 'Penicillin', 'Sulfa', 'Aspirin').
    """
    q = drug_name.strip().lower()
    matched_drug = None

    for drug in PAKISTANI_FORMULARY:
        if q in drug["brand"].lower() or q in drug["generic"].lower():
            matched_drug = drug
            break

    allergies_lower = [a.lower() for a in patient_allergies]
    contraindications = []

    # Penicillin cross-reactivity
    if any("penicillin" in a for a in allergies_lower):
        if matched_drug and "Penicillin" in matched_drug.get("class", ""):
            contraindications.append({
                "allergen": "Penicillin",
                "risk": "CONTRAINDICATED (High risk of severe anaphylaxis/angioedema)",
                "explanation": f"{drug_name} belongs to the Penicillin class and must not be administered."
            })
        elif matched_drug and "Cephalosporin" in matched_drug.get("class", ""):
            contraindications.append({
                "allergen": "Penicillin",
                "risk": "CAUTION (Cross-reactivity ~1-3%)",
                "explanation": f"{drug_name} is a Cephalosporin. Use with extreme caution in patients with confirmed Penicillin allergy."
            })

    # Sulfa allergy
    if any("sulfa" in a for a in allergies_lower):
        if matched_drug and ("Sulfonamide" in matched_drug.get("class", "") or "septran" in q or "sulfamethoxazole" in q):
            contraindications.append({
                "allergen": "Sulfa",
                "risk": "CONTRAINDICATED (High risk of Stevens-Johnson syndrome and severe hypersensitivity)",
                "explanation": f"{drug_name} contains Sulfamethoxazole/Sulfonamides."
            })

    # Aspirin / NSAID allergy
    if any("aspirin" in a or "nsaid" in a for a in allergies_lower):
        if matched_drug and ("NSAID" in matched_drug.get("class", "") or "Antiplatelet" in matched_drug.get("class", "")):
            contraindications.append({
                "allergen": "Aspirin/NSAID",
                "risk": "CONTRAINDICATED (Risk of acute bronchospasm, urticaria, or anaphylactoid reaction)",
                "explanation": f"{drug_name} is an NSAID/salicylate."
            })

    return {
        "status": "success",
        "drug_evaluated": drug_name,
        "patient_allergies": patient_allergies,
        "is_safe": len(contraindications) == 0,
        "contraindications_found": len(contraindications),
        "contraindications": contraindications,
        "recommendation": "DO NOT DISPENSE. Select alternative drug class." if contraindications else "No allergy conflicts detected."
    }


if __name__ == "__main__":
    server.run()
