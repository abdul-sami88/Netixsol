import re
from typing import Dict, Any, List

# 1. Comprehensive Perso-Arabic Urdu Script Translation Map
URDU_SCRIPT_MAP = {
    # Greetings & Identity
    r'السلام\s*علیکم': 'Assalam-o-Alaikum',
    r'سلام': 'Salam',
    r'کون\s*بول\s*رہا\s*ہے': 'who is speaking',
    r'کون\s*بات\s*کر\s*رہا\s*ہے': 'who is speaking',
    r'آپ\s*کون\s*ہیں': 'who are you',
    r'کون\s*ہے': 'who is this',

    # Supported Cities (Database Covered)
    r'لاہور': 'Lahore',
    r'اسلام\s*آباد': 'Islamabad',
    r'کراچی': 'Karachi',

    # Out-of-Coverage Pakistani Cities (Script)
    r'پشاور': 'Peshawar',
    r'ملتان': 'Multan',
    r'فیصل\s*آباد': 'Faisalabad',
    r'راولپنڈی': 'Rawalpindi',
    r'کوئٹہ': 'Quetta',
    r'سیالکوٹ': 'Sialkot',
    r'گوجرانوالہ': 'Gujranwala',
    r'حیدر\s*آباد': 'Hyderabad',
    r'سکھر': 'Sukkur',
    r'ایبٹ\s*آباد': 'Abbottabad',
    r'مردان': 'Mardan',
    r'بہاولپور': 'Bahawalpur',
    r'سرگودھا': 'Sargodha',
    
    # Areas
    r'ڈی\s*ایچ\s*اے': 'DHA',
    r'بحریہ\s*ٹاؤن': 'Bahria Town',
    r'بحریہ': 'Bahria Town',
    r'گلبرگ': 'Gulberg',
    r'کلفٹن': 'Clifton',
    
    # Property Types
    r'مکان': 'house',
    r'گھر': 'house',
    r'کوٹھی': 'house',
    r'اپارٹمنٹ': 'apartment',
    r'فلیٹ': 'apartment',
    r'پلاٹ': 'plot',
    r'زمین': 'plot',
    r'دکان': 'commercial shop',
    r'کمرشل': 'commercial',
    
    # Purpose & Actions
    r'خریدنا': 'buy',
    r'خریدنی': 'buy',
    r'چاہیے': 'want',
    r'فروخت': 'sale',
    r'کرایہ': 'rent',
    r'دکھائیں': 'show options',
    r'بتائیں': 'tell me',
    
    # Numbers & Prices
    r'کروڑ': 'crore',
    r'لاکھ': 'lakh',
    r'ملین': 'million',
    r'قیمت': 'price',
    r'بجٹ': 'budget',
    r'رقم': 'amount',
    r'ایک': '1', r'دو': '2', r'تین': '3', r'چار': '4', r'پانچ': '5',
    r'چھ': '6', r'سات': '7', r'آٹھ': '8', r'نو': '9', r'دس': '10',
    r'۱': '1', r'۲': '2', r'۳': '3', r'۴': '4', r'۵': '5',
    r'۶': '6', r'۷': '7', r'۸': '8', r'۹': '9', r'۰': '0',
    
    # Size
    r'مرلہ': 'marla',
    r'کنال': 'kanal',
    
    # Common Intent Keywords
    r'اقساط': 'installments',
    r'قسط': 'installment',
    r'ڈاؤن\s*پیمنٹ': 'down payment',
    r'سستا': 'cheaper',
    r'سستی': 'cheaper',
    r'بیڈ\s*روم': 'bedroom',
    r'کمرے': 'bedrooms',
    r'کاغذی': 'documents',
    r'کاغذات': 'documents',
    r'ٹرانسفر': 'transfer',
    r'میٹنگ': 'meeting',
    r'ملاقات': 'appointment',
}

# 2. Phonetic Slang Map for Supported Cities (Roman Urdu)
CITY_NORMALIZATION_MAP = {
    r'\blahorayyy?\b': 'Lahore',
    r'\blahoray\b': 'Lahore',
    r'\blahorey\b': 'Lahore',
    r'\blahor\b': 'Lahore',
    r'\blhr\b': 'Lahore',
    r'\bisloo\b': 'Islamabad',
    r'\bislamabadd?\b': 'Islamabad',
    r'\bisb\b': 'Islamabad',
    r'\bkarachii?\b': 'Karachi',
    r'\bkhi\b': 'Karachi',
}

# 3. Known Out-of-Coverage Cities (Roman Urdu)
UNSUPPORTED_CITIES = [
    "peshawar", "multan", "faisalabad", "rawalpindi", "pindi", "quetta", "sialkot",
    "gujranwala", "hyderabad", "sukkur", "abbottabad", "mardan", "bahawalpur", "sargodha", "swat", "murree"
]

# 4. Roman Urdu Term Normalization Map
URDU_TERM_MAP = {
    r'\bkaror\b': 'crore',
    r'\bkror\b': 'crore',
    r'\bcror\b': 'crore',
    r'\bkrore\b': 'crore',
    r'\blaac\b': 'lakh',
    r'\blac\b': 'lakh',
    r'\blacs\b': 'lakhs',
    r'\bkamra\b': 'bedroom',
    r'\bkamray\b': 'bedrooms',
    r'\bkamre\b': 'bedrooms',
    r'\bghar\b': 'house',
    r'\bmakan\b': 'house',
    r'\bzameen\b': 'plot',
    r'\bdukan\b': 'commercial shop',
    r'\bkiraya\b': 'rent',
    r'\bkhareedna\b': 'buy',
    r'\bqimat\b': 'price',
    r'\bqeemat\b': 'price',
}

# 5. Interruption Keywords
INTERRUPTION_KEYWORDS = [
    'ruko', 'rokain', 'roko', 'wait', 'ek second', 'ek minute', 
    'suno', 'meri baat suno', 'stop', 'hold on', 'baat suno', 'روکو', 'رکیں', 'ایک منٹ'
]

class STTProcessor:
    @staticmethod
    def normalize_transcript(raw_text: str) -> Dict[str, Any]:
        """
        Processes raw STT transcripts from Deepgram (Urdu Script & Roman Urdu).
        Normalizes words, extracts intent, detects out-of-coverage cities, and standardizes terms.
        """
        if not raw_text:
            return {
                "raw_transcript": "",
                "normalized_transcript": "",
                "is_interruption": False,
                "detected_city": None,
                "unsupported_city": None,
                "intent": "GENERAL"
            }

        text = raw_text.strip()
        text_lower = text.lower()
        
        # 1. Interruption Detection
        is_interruption = any(kw in text_lower or kw in text for kw in INTERRUPTION_KEYWORDS)
        
        # 2. Perso-Arabic Urdu Script to Roman Urdu Translation
        normalized_text = text
        for pattern, replacement in URDU_SCRIPT_MAP.items():
            normalized_text = re.sub(pattern, replacement, normalized_text)

        # 3. Roman Urdu Supported City Normalization
        detected_city = None
        for pattern, replacement in CITY_NORMALIZATION_MAP.items():
            if re.search(pattern, normalized_text, flags=re.IGNORECASE):
                detected_city = replacement
                normalized_text = re.sub(pattern, replacement, normalized_text, flags=re.IGNORECASE)

        # 4. Roman Urdu Terms Normalization
        for pattern, replacement in URDU_TERM_MAP.items():
            normalized_text = re.sub(pattern, replacement, normalized_text, flags=re.IGNORECASE)

        # 5. Detect Supported City if written standardly
        if not detected_city:
            for city_name in ["Lahore", "Islamabad", "Karachi"]:
                if city_name.lower() in normalized_text.lower():
                    detected_city = city_name
                    break

        # 6. Detect Out-of-Coverage Cities (e.g. Multan, Peshawar, Rawalpindi)
        unsupported_city = None
        norm_lower = normalized_text.lower()
        for u_city in UNSUPPORTED_CITIES:
            if u_city in norm_lower:
                unsupported_city = u_city.title()
                break

        # 7. Intent Classification
        intent = "GENERAL"
        if any(w in norm_lower for w in ["who is speaking", "who are you", "kon baat kar raha hai", "ap kon hain", "salam"]):
            intent = "GREETING_IDENTITY"
        elif any(w in norm_lower for w in ["price", "kitne ka", "qeemat", "amount"]):
            intent = "PRICE_INQUIRY"
        elif any(w in norm_lower for w in ["installment", "qist", "down payment"]):
            intent = "INSTALLMENT_INQUIRY"
        elif any(w in norm_lower for w in ["document", "transfer", "noc", "paper"]):
            intent = "LEGAL_DOCUMENTS"
        elif any(w in norm_lower for w in ["meeting", "visit", "appointment"]):
            intent = "APPOINTMENT"

        return {
            "raw_transcript": raw_text,
            "normalized_transcript": normalized_text,
            "is_interruption": is_interruption,
            "detected_city": detected_city,
            "unsupported_city": unsupported_city,
            "intent": intent
        }
