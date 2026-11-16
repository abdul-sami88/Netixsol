"""
ShopKaro E-Commerce Production Guardrails Engine
Implements 6 enterprise-grade defensive guardrail layers:
1. Security & Prompt Injection Defense (jailbreaks, DAN, system prompt leaks)
2. SQL & Code Injection Protection (SQL patterns, script tags, exec calls)
3. PII (Personally Identifiable Information) Redaction (Pakistani CNIC, 16-digit Cards, OTPs)
4. Toxicity & Profanity Filter (English, Urdu, and Roman Urdu abuse)
5. Out-of-Scope Off-Topic Deflection (programming, politics, religion, sports facts)
6. Competitor Deflection Guardrail (Daraz, Amazon, AliExpress inquiries)
"""

import re
from typing import Tuple, Optional, Dict, Any


class ShopKaroGuardrails:
    """
    Evaluates every inbound user query before it reaches tools or models.
    Returns (is_safe, sanitized_text, policy_response).
    """

    def __init__(self):
        # 1. Prompt Injection & Jailbreak Signatures
        self.jailbreak_patterns = [
            r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
            r"you\s+are\s+now\s+(in\s+)?(dan|developer\s+mode|unrestricted|jailbreak)",
            r"reveal\s+(your\s+)?(system\s+prompt|prompt|instructions|secret|api\s*key)",
            r"print\s+(the\s+)?(source\s+code|backend|database\s+password)",
            r"bypass\s+(all\s+)?(filters|rules|safety|guardrails)",
            r"act\s+as\s+an\s+unfiltered",
            r"pretend\s+you\s+have\s+no\s+rules",
        ]

        # 2. SQL & Script Injection Signatures
        self.injection_patterns = [
            r"\b(drop\s+table|delete\s+from|insert\s+into|alter\s+table|update\s+products)\b",
            r"(union\s+select|select\s+\*\s+from|or\s+1\s*=\s*1|--|\bexec\b|\bexecute\b)",
            r"(<script.*?>|javascript:|onload=|<iframe)",
        ]

        # 3. PII Regex Patterns
        self.pii_cnic_pattern = r"\b\d{5}[-\s]?\d{7}[-\s]?\d\b"  # Pakistani CNIC format (e.g. 42101-1234567-1)
        self.pii_card_pattern = r"\b(?:\d{4}[-\s]?){3}\d{4}\b"    # 16-digit Credit/Debit card numbers
        self.pii_cvv_pattern = r"\bcvv[:\s]*\d{3,4}\b"
        self.pii_otp_pattern = r"\b(?:otp|pin)[:\s]*\d{4,6}\b"

        # 4. Toxicity & Abusive Language (English & Roman Urdu)
        self.toxicity_patterns = [
            r"\b(chutiya|kameena|kutta|haramzada|bhenchod|madarchod|beghairat|ganda|fuck|bitch|bastard|asshole|idiot|stupid)\b",
            r"\b(kill\s+yourself|die|mar\s+jao|bakwas\s+band\s+karo)\b"
        ]

        # 5. Out-of-Scope Domains (Technical, General Knowledge, Politics)
        self.offtopic_keywords = [
            "python", "java", "c++", "javascript", "coding", "syntax", "algorithm",
            "debug", "compiler", "github", "stack overflow",
            "prime minister", "president", "election", "imran khan", "nawaz sharif", "vote",
            "what is football", "what is cricket", "who won the match", "who is",
            "capital of", "weather today", "tell me a joke", "write a poem", "essay on",
            "medical prescription", "dawa batao", "cure for", "lawyer advice"
        ]

        # 6. Competitors
        self.competitor_keywords = ["daraz", "amazon", "aliexpress", "telemart", "ishopping"]

    def sanitize_pii(self, text: str) -> str:
        """Masks sensitive customer personal information to prevent logging leaks."""
        sanitized = re.sub(self.pii_cnic_pattern, "[CNIC REDACTED]", text, flags=re.IGNORECASE)
        sanitized = re.sub(self.pii_card_pattern, "[CARD REDACTED]", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(self.pii_cvv_pattern, "[CVV REDACTED]", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(self.pii_otp_pattern, "[OTP REDACTED]", sanitized, flags=re.IGNORECASE)
        return sanitized

    def check_query(self, user_message: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validates incoming user query against all guardrails.
        Returns:
            (is_safe, sanitized_text, blocked_policy_response)
        """
        raw_text = user_message.strip()
        msg_lower = raw_text.lower()

        # Guardrail 0: Input Length / DoS Protection
        if len(raw_text) > 600:
            return False, raw_text[:600], "Aap ka pegham bohot taweel hai. Barah-e-karam apna sawal mukhtasir (under 600 characters) likhein."

        # Guardrail 1: Prompt Injection & Jailbreak Defense
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, msg_lower):
                return False, raw_text, (
                    "Security Alert: System prompt aur security instructions ko tabdeel karna mana hai. "
                    "Main sirf ShopKaro e-commerce platform ke mutabiq khidmaat faraham kar sakta hoon."
                )

        # Guardrail 2: SQL & Code Injection Prevention
        for pattern in self.injection_patterns:
            if re.search(pattern, msg_lower):
                return False, raw_text, (
                    "Security Notice: Malicious payload ya database injection detect hui hai. "
                    "Aap ka request reject kar diya gaya hai."
                )

        # Guardrail 3: Toxicity & Profanity Guardrail
        for pattern in self.toxicity_patterns:
            if re.search(pattern, msg_lower):
                return False, raw_text, (
                    "Barah-e-karam munasib aur tehzeeb-yafta alfaaz ka istemal karein. "
                    "ShopKaro par bad-tehzeebi aur abuse sakhti se mana hai. Hum aap ki behtar rehnumai ke liye tayar hain."
                )

        # Guardrail 4: Competitor Inquiries Deflection
        for comp in self.competitor_keywords:
            if re.search(r'\b' + re.escape(comp) + r'\b', msg_lower):
                return False, raw_text, (
                    f"ShopKaro Pakistan ka premier multi-category marketplace hai jo verified genuine brands, "
                    f"express delivery aur 100% money-back guarantee faraham karta hai. Hum doosray platforms (jaise {comp.capitalize()}) "
                    f"par tabsera nahi karte, lekin aap ko ShopKaro par behtareen discounts aur original products zaroor milenge!"
                )

        # Guardrail 5: Out-of-Scope Off-Topic Guardrail
        # (Only flag if message does NOT contain shopping intent words like buy, price, order, etc.)
        shopping_cues = ["buy", "khareed", "lena", "price", "pkr", "rate", "shop", "order", "product", "item", "sasta", "budget", "deliver", "dastiyab", "stock", "kurti", "shoes", "phone"]
        if any(re.search(r'\b' + re.escape(ot) + r'\b', msg_lower) for ot in self.offtopic_keywords):
            if not any(sc in msg_lower for sc in shopping_cues):
                return False, raw_text, (
                    "Main ShopKaro ka AI Shopping Assistant hoon. Main sirf ShopKaro par shopping karne, "
                    "products dhoondnay, orders track karne aur reviews janchnay mein aap ki madad kar sakta hoon.\n\n"
                    "Main general knowledge, programming ya political sawalaat ka jawab nahi de sakta. "
                    "Agar aap ko Fashion (Lawn, Kurtis, Shoes), Electronics (Smartphones, Earbuds, Laptops), "
                    "Beauty & Attar, Home Decor ya Groceries mein se kuch shopping karni ho toh barah-e-karam zaroor batayein!"
                )

        # Guardrail 6: PII Sanitization
        sanitized_msg = self.sanitize_pii(raw_text)

        # All checks passed
        return True, sanitized_msg, None


# Global singleton guardrail engine
global_guardrails = ShopKaroGuardrails()

