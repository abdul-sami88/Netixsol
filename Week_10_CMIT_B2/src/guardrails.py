"""
Zarya Digital Bank - Guardrails Engine (Inbound, Outbound, & PII Masking)
Week 10 - Day 4: Task 4 Guardrails Implementation
"""

import re
from typing import Dict, Any, Tuple, Optional


# Fixed institutional scam warning required by SBP regulations
SCAM_WARNING_RESPONSE = (
    "Zarya Bank kabhi bhi call ya SMS par aap ka OTP ya PIN nahi maangta. "
    "Yeh fraud ho sakta hai — kisi ko na batayein aur foran helpline par report karein."
)

CREDENTIAL_HARVEST_WARNING = (
    "Aap ka shukriya. Lekin security policy ke tehat Zarya Bank ka official AI assistant "
    "kabhi bhi aap ka PIN, password, OTP, ya card ka CVV number nahi maangta aur na hi process karta hai. "
    "Bara-e-meherbani yeh sensitive maloomat kisi ke sath share na karein."
)

PROMPT_INJECTION_WARNING = (
    "Aap ki request process nahi ki ja sakti kyonkay yeh Zarya Digital Bank ki "
    "system security policy ke khilaf hai. Sirf banking related sawalat poochein."
)

OFF_TOPIC_WARNING = (
    "Main Zarya Digital Bank ka AI banking assistant hoon. Main sirf banking, accounts, "
    "cards, aur fund transfers ke mutaliq sawalat ke jawabat de sakta hoon."
)


class ZaryaGuardrails:
    """
    Comprehensive Inbound and Outbound Security Guardrails for Zarya Digital Bank.
    """

    # Inbound patterns: Prompt Injection / System Jailbreaks
    PROMPT_INJECTION_PATTERNS = [
        r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
        r"(?i)\byou\s+are\s+now\s+(dan|unrestricted|developer\s+mode|jailbroken)\b",
        r"(?i)\brepeat\s+(your\s+)?(system\s+prompt|initial\s+instructions)\b",
        r"(?i)\bdisregard\s+(the\s+)?rules\b",
        r"(?i)\bact\s+as\s+an\s+unfiltered\b",
        r"(?i)\bshow\s+me\s+your\s+(prompt|instructions|hidden\s+rules)\b",
    ]

    # Inbound patterns: Requests asking for or providing PIN, OTP, CVV, Password
    CREDENTIAL_PATTERNS = [
        r"(?i)\b(mera\s+)?(pin|otp|cvv|password)\s+(le\s+lo|mang|batao|share)\b",
        r"(?i)\b(enter|share|give|send|dedo)\s+(me\s+)?(pin|otp|cvv|password)\b",
        r"(?i)\bcard\s+number\s+aur\s+cvv\b",
        r"(?i)\b(4-digit|six-digit)\s+(pin|code)\b",
    ]

    # Inbound patterns: Scam, Lottery, Money Mule (Account Renting)
    SCAM_PATTERNS = [
        r"(?i)\b(jeeto\s+pakistan|inam\s+nikla|lottery|prize\s+bond|sona\s+nikla)\b",
        r"(?i)\b(tax\s+transfer|advance\s+fee|processing\s+fee\s+bhejo)\b",
        r"(?i)\b(rent\s+pe\s+de\s*do|account\s+rent|kiraye\s+par\s+account|50\s*hazar\s+mahina)\b",
        r"(?i)\b(money\s+mule|trading\s+ke\s+liye\s+account\s+use)\b",
    ]

    # Inbound patterns: Harmful / Off-topic
    OFF_TOPIC_PATTERNS = [
        r"(?i)\b(write\s+a\s+poem|cook|recipe|weather|cricket\s+score|write\s+python\s+code)\b",
        r"(?i)\b(who\s+won\s+the\s+match|essay\s+on|love\s+letter)\b",
        r"(?i)\b(bomb|weapon|hack|exploit|illegal|drug)\b",
    ]

    # Outbound patterns: Leaking full card numbers, CVVs, or account numbers
    LEAKAGE_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    LEAKAGE_CVV_PATTERN = re.compile(r"(?i)\b(cvv\s*[:=]?\s*\d{3,4})\b")

    # PII patterns for logs
    CNIC_REGEX = re.compile(r"\b\d{5}-\d{7}-\d{1}\b")
    PHONE_REGEX = re.compile(r"\b(?:03\d{2}[-\s]?\d{7}|\+92\d{10})\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    def inspect_inbound(self, user_prompt: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluates inbound user prompt.
        Returns:
            (is_safe: bool, blocked_reason: Optional[str], response: Optional[str])
        """
        clean_text = user_prompt.strip()

        # 1. Prompt Injection Check
        for pat in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pat, clean_text):
                return False, "PROMPT_INJECTION", PROMPT_INJECTION_WARNING

        # 2. Credential Phishing / Harvesting Check
        for pat in self.CREDENTIAL_PATTERNS:
            if re.search(pat, clean_text):
                return False, "CREDENTIAL_HARVESTING", CREDENTIAL_HARVEST_WARNING

        # 3. Known Scam / Money Mule Check
        for pat in self.SCAM_PATTERNS:
            if re.search(pat, clean_text):
                return False, "SCAM_DETECTION", SCAM_WARNING_RESPONSE

        # 4. Off-topic check
        for pat in self.OFF_TOPIC_PATTERNS:
            if re.search(pat, clean_text):
                return False, "OFF_TOPIC", OFF_TOPIC_WARNING

        return True, None, None

    def inspect_outbound(self, model_response: str) -> str:
        """
        Sanitizes model response to prevent institutional leakage.
        Replaces raw card numbers with masked version (e.g. ****-****-****-1234).
        """
        def mask_card(match):
            raw = match.group(0).replace("-", "").replace(" ", "")
            return f"****-****-****-{raw[-4:]}"

        sanitized = self.LEAKAGE_CARD_PATTERN.sub(mask_card, model_response)
        sanitized = self.LEAKAGE_CVV_PATTERN.sub("[REDACTED_CVV]", sanitized)
        return sanitized

    def mask_pii_for_logging(self, text: str) -> str:
        """
        Redacts PII (CNIC, Pakistani Phone numbers, Emails) for audit logging.
        """
        def mask_cnic(match):
            cnic = match.group(0)
            return f"{cnic[:5]}-*******-{cnic[-1]}"

        def mask_phone(match):
            phone = match.group(0)
            return f"{phone[:4]}*****{phone[-2:]}"

        def mask_email(match):
            email = match.group(0)
            parts = email.split("@")
            user = parts[0]
            domain = parts[1] if len(parts) > 1 else ""
            return f"{user[0]}***@{domain}"

        masked = self.CNIC_REGEX.sub(mask_cnic, text)
        masked = self.PHONE_REGEX.sub(mask_phone, masked)
        masked = self.EMAIL_REGEX.sub(mask_email, masked)
        return masked
