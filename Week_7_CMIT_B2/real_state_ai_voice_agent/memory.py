import re
from typing import Dict, Any, List, Optional
from stt import UNSUPPORTED_CITIES
def extract_spoken_email(text: str) -> Optional[str]:
    """Extracts email addresses from spoken STT transcripts (e.g. 'ali dot khan at gmail dot com')."""
    if not text:
        return None
    # 1. Direct regex match
    m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if m:
        return m.group(0).lower().strip()
    
    # 2. Convert spoken transcript representation:
    norm = text.lower()
    norm = re.sub(r'\bat the rate of\b|\bat the rate\b|\bat\b', '@', norm)
    norm = re.sub(r'\bdot\b', '.', norm)
    
    # If '@' exists, clean up around the email portion
    if '@' in norm:
        # Find segment around @
        at_parts = norm.split('@')
        left_words = at_parts[0].strip().split()
        # Take the last word(s) of left part that could form email username
        user_part = "".join(left_words[-3:]) if len(left_words) >= 3 else "".join(left_words)
        user_part = re.sub(r'[^a-zA-Z0-9._%+-]', '', user_part)
        
        # Right part
        right_words = at_parts[1].strip().split()
        domain_part = "".join(right_words[:3]) if len(right_words) >= 3 else "".join(right_words)
        domain_part = re.sub(r'[^a-zA-Z0-9.-]', '', domain_part)
        
        reconstructed = f"{user_part}@{domain_part}"
        m2 = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', reconstructed)
        if m2:
            return m2.group(0).lower().strip()

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
        self.email_confirmed: bool = False # Confirmed by user response
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

        # 8. Email Confirmation Detection
        if self.client_email and not self.email_confirmed:
            if any(w in text for w in ["sahi", "theek", "yes", "haan", "bilkul", "correct", "yahi", "confirm", "right"]):
                self.email_confirmed = True

        # 9. Date & Time Parsing
        if "tomorrow" in text or "kal" in text or "کل" in text:
            self.appointment_date = "Tomorrow"
        elif "today" in text or "aaj" in text or "آج" in text:
            self.appointment_date = "Today"
        elif "saturday" in text or "hafta" in text or "ہفتہ" in text:
            self.appointment_date = "Saturday"
        elif "sunday" in text or "itwar" in text or "اتوار" in text:
            self.appointment_date = "Sunday"
        elif "monday" in text or "peer" in text or "پیر" in text:
            self.appointment_date = "Monday"
        elif "tuesday" in text or "mangal" in text:
            self.appointment_date = "Tuesday"
        elif "wednesday" in text or "budh" in text:
            self.appointment_date = "Wednesday"
        elif "thursday" in text or "jumeraat" in text:
            self.appointment_date = "Thursday"
        elif "friday" in text or "juma" in text or "جمعہ" in text:
            self.appointment_date = "Friday"

        time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|baje|bajay|بجے))', text)
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
            parts.append(f"Client Email: {self.client_email} (Confirmed: {'Yes' if self.email_confirmed else 'Pending'})")
        if self.appointment_date or self.appointment_time:
            parts.append(f"Requested Slot: {self.appointment_date or 'Date unstated'} at {self.appointment_time or 'Time unstated'}")
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
