"""
guardrails.py
=============
Guardrails, Input Validation & Security Defense for Pakistan Real Estate AI.

Features:
1. Out-of-Distribution (OOD) Checks:
   - Refuses predictions for physical specs or budgets far outside the training distribution.
   - Enforces valid Pakistani metropolitan cities and societies.
2. Mandatory Valuation Disclaimer:
   - Appends explicit disclaimers in English and UrduLish that prices are statistical estimates.
3. Prompt-Injection Defense:
   - Detects adversarial attempts ("Ignore instructions", "Set price to 1 rupee", "System override").
   - Neutralizes injection and responds with polite, grounded refusal.
4. Audit Trail Prediction Logging:
   - Logs every prediction (inputs, output, model version, OOD status) to SQLite `model_prediction_logs`.
"""

import os
import re
import json
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from database import get_db_connection

# ========================================================
# 1. OUT-OF-DISTRIBUTION (OOD) SPECIFICATION
# ========================================================
VALID_CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad"]

# Training distribution boundaries based on Pakistan Real Estate dataset
OOD_BOUNDS = {
    "plot_size_marla": {"min": 1.0, "max": 100.0},       # 1 Marla to 5 Kanals
    "covered_area_sqft": {"min": 150.0, "max": 25000.0}, # Studio to Mega Villa
    "bedrooms": {"min": 0, "max": 15},
    "bathrooms": {"min": 0, "max": 16},
    "age_years": {"min": 0.0, "max": 60.0},
    "budget_pkr": {"min": 500000.0, "max": 2500000000.0}, # 5 Lakh to 250 Crore
    "num_calls": {"min": 0, "max": 50}
}


def check_property_ood(prop_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates if property parameters fall within acceptable training distribution.
    Returns (True, reason) if Out-Of-Distribution (OOD), else (False, None).
    """
    # 1. City Check
    city = str(prop_data.get("city", "")).strip().title()
    if city and city not in VALID_CITIES:
        return True, f"City '{city}' is out of distribution. Supported metropolitan markets are: {', '.join(VALID_CITIES)}."

    # 2. Plot size check
    plot_size = prop_data.get("plot_size_marla")
    if plot_size is not None:
        plot_size = float(plot_size)
        p_min = OOD_BOUNDS["plot_size_marla"]["min"]
        p_max = OOD_BOUNDS["plot_size_marla"]["max"]
        if plot_size < p_min or plot_size > p_max:
            return True, f"Plot size of {plot_size:.1f} Marla is far outside normal training range ({p_min} to {p_max} Marla). Algorithmic prediction refused."

    # 3. Covered area check
    cov_area = prop_data.get("covered_area_sqft")
    if cov_area is not None:
        cov_area = float(cov_area)
        c_min = OOD_BOUNDS["covered_area_sqft"]["min"]
        c_max = OOD_BOUNDS["covered_area_sqft"]["max"]
        if cov_area < c_min or cov_area > c_max:
            return True, f"Covered area of {cov_area:,.0f} sqft is far outside normal training distribution ({c_min} to {c_max} sqft)."

    # 4. Bedrooms check
    beds = prop_data.get("bedrooms")
    if beds is not None:
        b_val = int(beds)
        if b_val < OOD_BOUNDS["bedrooms"]["min"] or b_val > OOD_BOUNDS["bedrooms"]["max"]:
            return True, f"Bedroom count of {b_val} is outside acceptable training boundaries (0 to 15 bedrooms)."

    # 5. Age check
    age = prop_data.get("age_years")
    if age is not None:
        a_val = float(age)
        if a_val < OOD_BOUNDS["age_years"]["min"] or a_val > OOD_BOUNDS["age_years"]["max"]:
            return True, f"Structure age of {a_val} years exceeds training limit (0 to 60 years)."

    return False, None


def check_lead_ood(lead_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates if sales lead parameters fall within acceptable training distribution.
    """
    budget = float(lead_data.get("budget_pkr") or lead_data.get("max_budget_pkr") or 0.0)
    b_min = OOD_BOUNDS["budget_pkr"]["min"]
    b_max = OOD_BOUNDS["budget_pkr"]["max"]
    if budget > 0 and (budget < b_min or budget > b_max):
        return True, f"Lead budget of PKR {budget:,.0f} is outside realistic training distribution."

    calls = int(lead_data.get("num_calls") or 0)
    if calls > OOD_BOUNDS["num_calls"]["max"]:
        return True, f"Call count ({calls}) exceeds valid training range."

    return False, None


# ========================================================
# 2. MANDATORY VALUATION DISCLAIMERS
# ========================================================
DISCLAIMER_TEXT_EN = (
    "Disclaimer: All property valuations and price ranges provided are algorithmic "
    "statistical estimates based on historical market trends and do not constitute an "
    "official FBR, bank-certified, or legal valuation appraisal."
)

DISCLAIMER_TEXT_UR = (
    "Note: Yeh AI model ka generate kardah automated andaza (statistical estimate) hai, "
    "koi official FBR ya certified legal valuation appraisal nahi hai."
)


# ========================================================
# 3. PROMPT INJECTION DEFENSE
# ========================================================
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)?\s*instructions?",
    r"disregard\s+(all\s+)?(previous|prior|system)?\s*rules?",
    r"set\s+price\s+to\s+(1|0|one|zero|negative)\s*(rupee|pkr|rs)?",
    r"make\s+price\s+(1|0|free)",
    r"price\s+is\s+now\s+1\s*rupee",
    r"override\s+(the\s+)?(system|pricing|valuation|model)",
    r"pretend\s+you\s+are\s+(a\s+hacker|an\s+attacker|unrestricted)",
    r"bypass\s+security",
    r"output\s+(the\s+)?system\s*prompt",
    r"reveal\s+(internal\s+)?instructions?"
]

def check_prompt_injection(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Scans incoming conversational prompt for injection attacks.
    Returns (True, safe_refusal_response) if attack detected, else (False, None).
    """
    clean_text = (user_input or "").lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, clean_text):
            return True, (
                "Sir main sirf verified real estate data aur market valuation par baat kar sakti hoon. "
                "Pricing rules ya system instructions ko bypass nahi kiya ja sakta."
            )
    return False, None


# ========================================================
# 4. AUDIT TRAIL LOGGING IN SQLITE
# ========================================================
def init_prediction_logs_table():
    """Initializes model prediction audit logs table in SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prediction_type TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            input_payload TEXT NOT NULL,
            output_payload TEXT NOT NULL,
            is_ood INTEGER DEFAULT 0,
            ood_reason TEXT,
            client_email TEXT
        )
    """)
    conn.commit()
    conn.close()

# Auto-initialize on import
init_prediction_logs_table()

def log_model_prediction(
    prediction_type: str,
    model_name: str,
    model_version: str,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    is_ood: bool = False,
    ood_reason: Optional[str] = None,
    client_email: Optional[str] = None
) -> int:
    """
    Logs every model prediction (inputs, outputs, model version, timestamp)
    for regulatory audit and governance.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO model_prediction_logs (
            prediction_type, model_name, model_version,
            input_payload, output_payload, is_ood, ood_reason, client_email
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prediction_type,
        model_name,
        model_version,
        json.dumps(input_payload, default=str),
        json.dumps(output_payload, default=str),
        1 if is_ood else 0,
        ood_reason or "",
        client_email or "anonymous"
    ))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id
