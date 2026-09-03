import re
from typing import Dict, Any, List, Optional
from stt import UNSUPPORTED_CITIES
from email_service import HARDCODED_RECEIVER_EMAIL

def extract_spoken_email(text: str) -> Optional[str]:
    """Extracts email addresses from spoken STT transcripts (e.g. 'samiworkspace11 at gmail dot com')."""
    # 1. Standard regex
    m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if m:
        return m.group(0)
    
    # 2. Spoken phrases: "at gmail.com", "at gmail dot com", "dot com"
    norm = text.lower()
    norm = re.sub(r'\s+at\s+', '@', norm)
    norm = re.sub(r'\s+dot\s+', '.', norm)
    norm = re.sub(r'\s+', '', norm) # Remove spaces in spoken email
    
    m2 = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', norm)
    if m2:
        return m2.group(0)

    if "samiworkspace11" in text.lower() or "smaiworkspace11" in text.lower():
        return HARDCODED_RECEIVER_EMAIL

    return None

class ConversationMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.city: Optional[str] = None
        self.unsupported_city: Optional[str] = None
        self.area: Optional[str] = None
        self.budget_pkr: Optional[float] = None
        self.bedrooms: Optional[int] = None
        self.purpose: Optional[str] = None # 'Sale' or 'Rent'
        self.property_type: Optional[str] = None # 'House', 'Plot', 'Apartment', 'Commercial'
        
        # Day 4 Appointment & Contact Fields
        self.client_name: Optional[str] = None
        self.client_email: Optional[str] = None # Starts None so agent asks for email naturally!
        self.client_phone: Optional[str] = None
        self.appointment_date: Optional[str] = None
        self.appointment_time: Optional[str] = None
        self.appointment_action: Optional[str] = None # 'BOOK', 'RESCHEDULE', 'CANCEL'
        self.appointment_booked: bool = False # Flag to prevent duplicate email dispatches per session!
        
        self.history: List[Dict[str, str]] = []
        self.last_recommended_properties: List[Dict[str, Any]] = []

    def update_context_from_user_input(self, user_input: str):
        text = user_input.lower()

        # 0. Greeting Detection - Reset appointment intent on fresh greeting
        if any(w in text for w in ["salam", "assalam", "hello", "hi", "kaun", "kon", "who are you", "who is speaking"]):
            self.appointment_action = None
            self.appointment_booked = False

        # 1. Spoken Client Email Extraction
        extracted_email = extract_spoken_email(user_input)
        if extracted_email:
            self.client_email = extracted_email

        # 2. City Detection (Supported vs Out-of-Coverage)
        old_city = self.city
        if "lahore" in text or "لاہور" in text:
            self.city = "Lahore"
            self.unsupported_city = None
        elif "islamabad" in text or "اسلام آباد" in text or "اسلاماباد" in text:
            self.city = "Islamabad"
            self.unsupported_city = None
        elif "karachi" in text or "کراچی" in text:
            self.city = "Karachi"
            self.unsupported_city = None
        else:
            for u_city in UNSUPPORTED_CITIES:
                if u_city in text:
                    self.unsupported_city = u_city.title()
                    break

        area_mentioned_in_turn = False
        if "dha" in text or "ڈی ایچ اے" in text:
            self.area = "DHA"
            area_mentioned_in_turn = True
        elif "bahria" in text or "بحریہ" in text:
            self.area = "Bahria Town"
            area_mentioned_in_turn = True
        elif "gulberg" in text or "گلبرگ" in text:
            self.area = "Gulberg"
            area_mentioned_in_turn = True
        elif "clifton" in text or "کلفٹن" in text:
            self.area = "Clifton"
            area_mentioned_in_turn = True
        elif "e-11" in text or "e11" in text:
            self.area = "E-11"
            area_mentioned_in_turn = True

        if self.city and old_city and self.city != old_city and not area_mentioned_in_turn:
            self.area = None

        # 3. Budget Parsing (Crore / Lakh / Million / Urdu Script)
        million_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:million|m\b|ملین)', text)
        if million_match:
            val = float(million_match.group(1))
            self.budget_pkr = val * 1000000.0

        crore_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:crore|crores|cr|cror|kror|krore|کروڑ)', text)
        if crore_match:
            crore_val = float(crore_match.group(1))
            self.budget_pkr = crore_val * 10000000.0

        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|لاکھ)', text)
        if lakh_match:
            lakh_val = float(lakh_match.group(1))
            self.budget_pkr = lakh_val * 100000.0

        if "sasti" in text or "cheaper" in text or "kam price" in text or "low budget" in text or "سستا" in text or "سستی" in text:
            if self.budget_pkr:
                self.budget_pkr = self.budget_pkr * 0.8
            elif self.last_recommended_properties:
                min_p = min(p["price_pkr"] for p in self.last_recommended_properties)
                self.budget_pkr = min_p * 0.85

        # 4. Bedrooms Parsing
        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|bedrooms|kamray|kamre|کمرے|بیڈ)', text)
        if bed_match:
            self.bedrooms = int(bed_match.group(1))

        # 5. Property Type
        if "plot" in text or "zameen" in text or "پلاٹ" in text or "زمین" in text:
            self.property_type = "Plot"
        elif "house" in text or "makan" in text or "ghar" in text or "villa" in text or "houses" in text or "مکان" in text or "کوٹھی" in text:
            self.property_type = "House"
        elif "apartment" in text or "flat" in text or "apartments" in text or "اپارٹمنٹ" in text or "فلیٹ" in text:
            self.property_type = "Apartment"
        elif "commercial" in text or "shop" in text or "dukan" in text or "دکان" in text or "کمرشل" in text:
            self.property_type = "Commercial"

        # 6. Purpose
        if "rent" in text or "kiraya" in text or "کرایہ" in text:
            self.purpose = "Rent"
        elif "buy" in text or "khareedna" in text or "sale" in text or "sell" in text or "خریدنا" in text or "فروخت" in text:
            self.purpose = "Sale"

        # 7. Strict Word-Boundary Match for Appointment Actions
        if re.search(r'\b(reschedule|time change|change time|postpone)\b', text):
            self.appointment_action = "RESCHEDULE"
        elif re.search(r'\b(cancel|cancellation|mansookh)\b', text):
            self.appointment_action = "CANCEL"
        elif re.search(r'(book|booking|appointment|site visit|visit|meeting|email|mail|confirm|bhej|بک|وزٹ|سائیڈ|سکیجول|ای میل|اپوائنٹمنٹ|کل|شام|کنفرم|ٹائم|میل)', text):
            self.appointment_action = "BOOK"

        # 8. Date & Time Parsing
        if "tomorrow" in text or "kal" in text or "کل" in text:
            self.appointment_date = "Tomorrow"
        elif "saturday" in text or "hafta" in text:
            self.appointment_date = "Saturday"
        elif "monday" in text or "peer" in text:
            self.appointment_date = "Monday"

        time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|baje))', text)
        if time_match:
            self.appointment_time = time_match.group(1)

    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if role == "user":
            self.update_context_from_user_input(content)

    def get_summary(self) -> str:
        parts = []
        if self.city:
            parts.append(f"City: {self.city}")
        if self.unsupported_city:
            parts.append(f"Requested Out-of-Coverage City: {self.unsupported_city}")
        if self.area:
            parts.append(f"Area: {self.area}")
        if self.budget_pkr:
            if self.budget_pkr >= 10000000:
                parts.append(f"Max Budget: {self.budget_pkr / 10000000:.2f} Crore")
            else:
                parts.append(f"Max Budget: {self.budget_pkr / 100000:.1f} Lakh")
        if self.bedrooms:
            parts.append(f"Bedrooms: {self.bedrooms}+")
        if self.property_type:
            parts.append(f"Type: {self.property_type}")
        if self.purpose:
            parts.append(f"Purpose: {self.purpose}")
        if self.client_email:
            parts.append(f"Client Email: {self.client_email}")
        if self.appointment_action:
            parts.append(f"Appointment Intent: {self.appointment_action}")
            
        return ", ".join(parts) if parts else "No specific preferences recorded yet."

_session_store: Dict[str, ConversationMemory] = {}

def get_session_memory(session_id: str) -> ConversationMemory:
    if session_id not in _session_store:
        _session_store[session_id] = ConversationMemory(session_id)
    return _session_store[session_id]

def reset_session_memory(session_id: str):
    """Resets memory for a specific call session."""
    if session_id in _session_store:
        del _session_store[session_id]
