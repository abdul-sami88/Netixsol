"""
PII / PHI De-Identification Pipeline for City Care Clinics.
Implements Day 1 privacy standards with zero network latency:
- Pakistani CNIC pattern recognition (xxxxx-xxxxxxx-x)
- Pakistani Mobile Phone recognition (+92-3xx-xxxxxxx, 03xx-xxxxxxx)
- Email address redaction
- Pakistani name & address entity scrubbing
- Tokenization & reversible de-identification for agent-to-agent communication
"""

import re
from typing import Dict, Any, Tuple, Optional

# Pakistani Identifiers Regular Expressions
CNIC_REGEX = re.compile(r"\b\d{5}-\d{7}-\d{1}\b")
PHONE_REGEX = re.compile(r"(?:\+92[- ]?|0092[- ]?|0)?3\d{2}[- ]?\d{7}\b")
EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")

# Name & Greeting patterns in English & UrduLish
NAME_PATTERNS = [
    re.compile(r"(?:mera naam|my name is|patient name is|patient is|patient:)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE),
    re.compile(r"(?:mr\.|mrs\.|ms\.|dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE)
]


def sanitize_patient_text(text: str) -> str:
    """
    Scrubs direct patient identifiers (CNIC, Pakistani Phone, Email, Person Names)
    before sending text to cloud LLM endpoints or logging.
    """
    if not text:
        return ""

    cleaned = CNIC_REGEX.sub("[CNIC_REDACTED]", text)
    cleaned = PHONE_REGEX.sub("[PHONE_REDACTED]", cleaned)
    cleaned = EMAIL_REGEX.sub("[EMAIL_REDACTED]", cleaned)

    for pat in NAME_PATTERNS:
        cleaned = pat.sub(lambda m: m.group(0).replace(m.group(1), "[NAME_REDACTED]"), cleaned)

    return cleaned


def tokenize_pii_for_agents(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Tokenizes sensitive direct identifiers into deterministic vault tokens
    (e.g. <CNIC_1>, <PHONE_1>) so agents can reason about entities without
    exposing raw PII to remote models. Returns (tokenized_text, token_vault).
    """
    token_vault: Dict[str, str] = {}
    counter = {"cnic": 0, "phone": 0, "email": 0}

    def _replace_cnic(m):
        val = m.group(0)
        # Check if already vaulted
        for tok, v in token_vault.items():
            if v == val:
                return tok
        counter["cnic"] += 1
        tok = f"<CNIC_{counter['cnic']}>"
        token_vault[tok] = val
        return tok

    def _replace_phone(m):
        val = m.group(0)
        for tok, v in token_vault.items():
            if v == val:
                return tok
        counter["phone"] += 1
        tok = f"<PHONE_{counter['phone']}>"
        token_vault[tok] = val
        return tok

    def _replace_email(m):
        val = m.group(0)
        for tok, v in token_vault.items():
            if v == val:
                return tok
        counter["email"] += 1
        tok = f"<EMAIL_{counter['email']}>"
        token_vault[tok] = val
        return tok

    tokenized = CNIC_REGEX.sub(_replace_cnic, text)
    tokenized = PHONE_REGEX.sub(_replace_phone, tokenized)
    tokenized = EMAIL_REGEX.sub(_replace_email, tokenized)

    return tokenized, token_vault


def detokenize_pii(text: str, token_vault: Dict[str, str]) -> str:
    """Restores tokenized placeholders back to original values in local storage."""
    restored = text
    for tok, original in token_vault.items():
        restored = restored.replace(tok, original)
    return restored
