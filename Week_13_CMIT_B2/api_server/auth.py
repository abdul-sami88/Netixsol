"""
Role-Based Access Control (RBAC) & Authentication Module
Manages identity verification and authorization for:
- STUDENT: Can view learning path, chat with Socratic tutor, submit assignments
- TEACHER: Can view class mastery, access grading queue, review at-risk alerts and plagiarism
- ADMIN: System configuration, IRT question calibration, sandbox policies
"""

import hmac
import hashlib
import base64
import json
import time
from typing import Dict, Any, Optional

SECRET_KEY = "ilm_academy_super_secret_jwt_key_2026"

USERS_DB = {
    "ali@ilm.edu": {
        "user_id": "STU-1001",
        "name": "Ali Raza",
        "role": "STUDENT",
        "password_hash": "e10adc3949ba59abbe56e057f20f883e", # '123456'
        "cohort": "Intermediate W3"
    },
    "sara@ilm.edu": {
        "user_id": "STU-1002",
        "name": "Sara Ahmed",
        "role": "STUDENT",
        "password_hash": "e10adc3949ba59abbe56e057f20f883e",
        "cohort": "Fast-Track W3"
    },
    "instructor@ilm.edu": {
        "user_id": "TEA-5001",
        "name": "Prof. Usman Qureshi",
        "role": "TEACHER",
        "password_hash": "e10adc3949ba59abbe56e057f20f883e",
        "department": "Computer Science"
    },
    "admin@ilm.edu": {
        "user_id": "ADM-0001",
        "name": "System Administrator",
        "role": "ADMIN",
        "password_hash": "e10adc3949ba59abbe56e057f20f883e",
        "permissions": ["ALL"]
    }
}

class RBACManager:
    """
    Handles token creation, validation, and role enforcement.
    """

    @staticmethod
    def create_token(user_id: str, email: str, role: str) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": int(time.time()) + (86400 * 7) # 7-day token
        }
        b64_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature_input = f"{b64_header}.{b64_payload}"
        sig = hmac.new(SECRET_KEY.encode(), signature_input.encode(), hashlib.sha256).digest()
        b64_sig = base64.urlsafe_b64encode(sig).decode().rstrip("=")
        return f"{b64_header}.{b64_payload}.{b64_sig}"

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            b64_header, b64_payload, b64_sig = parts
            signature_input = f"{b64_header}.{b64_payload}"
            expected_sig = hmac.new(SECRET_KEY.encode(), signature_input.encode(), hashlib.sha256).digest()
            expected_b64_sig = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

            if not hmac.compare_digest(b64_sig, expected_b64_sig):
                return None

            # Add padding back if necessary
            rem = len(b64_payload) % 4
            if rem > 0:
                b64_payload += "=" * (4 - rem)
            payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode()).decode())

            if payload.get("exp", 0) < time.time():
                return None # Expired

            return payload
        except Exception:
            return None

    @classmethod
    def authenticate(cls, email: str, password_raw: str) -> Optional[Dict[str, Any]]:
        user = USERS_DB.get(email.lower())
        if not user:
            return None
        # Verify password MD5
        pw_hash = hashlib.md5(password_raw.encode()).hexdigest()
        if user["password_hash"] != pw_hash:
            return None
        token = cls.create_token(user["user_id"], email, user["role"])
        return {
            "token": token,
            "user_id": user["user_id"],
            "name": user["name"],
            "role": user["role"],
            "email": email
        }
