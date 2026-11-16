"""
Query Understanding & Linguistic Variations Engine for Pakistani E-Commerce
Implements Task 1 Query Understanding:
- Roman Urdu & English spelling variation normalization ("joota" / "juta" / "shoes")
- Price range parsing ("20 hazaar", "1.5 lac", "under 5000", "5k tak")
- Attribute extraction: Category, Colour, Occasion, Gender/Target
"""

import re
from typing import Dict, Any, Optional, List, Tuple


# Synonyms and linguistic normalization dictionary
ROMAN_URDU_SYNONYMS = {
    # Footwear
    "joota": "shoes",
    "jootay": "shoes",
    "juta": "shoes",
    "jutay": "shoes",
    "chappal": "sandals",
    "khussa": "khussa shoes",
    "chapal": "sandals",
    "sneakers": "sneakers shoes",
    
    # Clothing / Apparel
    "kapray": "clothes clothing",
    "kapra": "fabric clothing",
    "kurta": "kurta",
    "kurti": "kurti",
    "kameez": "shalwar kameez",
    "shalwar": "shalwar",
    "lehenga": "lehenga bridal",
    "lehnga": "lehenga bridal",
    "lawn": "lawn unstitched",
    "suit": "suit 3-piece",
    "shawl": "shawl winter",
    "chador": "chador shawl",
    
    # Accessories & Tech
    "ghari": "watch smartwatches",
    "chashma": "sunglasses glasses",
    "basta": "school bag backpack",
    "thaila": "bag handbag",
    "tar": "cable charger",
    "dabba": "box packaging",
    
    # Qualifiers & Descriptors
    "sasta": "budget affordable",
    "sasti": "budget affordable",
    "saste": "budget affordable",
    "mehanga": "premium luxury",
    "mehangi": "premium luxury",
    "mehange": "premium luxury",
    "acha": "best high quality",
    "achi": "best high quality",
    "ache": "best high quality",
    "achey": "best high quality",
    "khoobsurat": "beautiful elegant stylish",
    "asli": "original authentic",
    "gift": "gift festive luxury collection",
    "celebration": "festive eid celebration wedding",
    "special": "limited edition festive luxury",
    "laptop": "laptop laptops notebook computer",
    "laptops": "laptop laptops notebook computer",
    "shoes": "shoes footwear",
    "shoe": "shoes footwear",
    "chappal": "shoes footwear",
    "chappalein": "shoes footwear",
    "sandals": "shoes footwear",
    "jutay": "shoes footwear",
    "jootay": "shoes footwear",
    "kurtay": "kurta clothing",
    "kapray": "apparel fabric clothing",
    "kapra": "fabric clothing",
}

# Color dictionary (English & Roman Urdu)
COLOR_MAPPINGS = {
    "red": "red",
    "surkh": "red",
    "lal": "red",
    "black": "black",
    "kala": "black",
    "kali": "black",
    "white": "white",
    "safaid": "white",
    "chitta": "white",
    "blue": "blue",
    "neela": "blue",
    "neeli": "blue",
    "green": "green",
    "sabz": "green",
    "pink": "pink",
    "gulabi": "pink",
    "yellow": "yellow",
    "peela": "yellow",
    "golden": "gold golden",
    "silver": "silver",
    "grey": "grey",
    "brown": "brown",
    "maroon": "maroon",
}

# Occasion dictionary
OCCASION_MAPPINGS = {
    "shaadi": "Wedding & Festive",
    "shadi": "Wedding & Festive",
    "wedding": "Wedding & Festive",
    "dulhan": "Wedding & Festive",
    "eid": "Eid Collection",
    "ramadan": "Ramadan Season",
    "ramzan": "Ramadan Season",
    "school": "Back to School",
    "college": "Back to School",
    "university": "Back to School",
    "bachon": "Kids & School",
    "bachay": "Kids & School",
    "office": "Formal Office",
    "casual": "Casual Daily Wear",
    "party": "Party Wear",
}

# Target gender / person dictionary
TARGET_MAPPINGS = {
    "ammi": "Women",
    "mama": "Women",
    "mother": "Women",
    "women": "Women",
    "womens": "Women",
    "ladies": "Women",
    "larki": "Women",
    "aurat": "Women",
    "khawateen": "Women",
    "abu": "Men",
    "baba": "Men",
    "father": "Men",
    "men": "Men",
    "mens": "Men",
    "mard": "Men",
    "larka": "Men",
    "bachon": "Kids",
    "bachi": "Kids",
    "baby": "Kids",
}

# Category keywords mapping
CATEGORY_KEYWORDS = {
    "Fashion": ["lawn", "kurta", "kurti", "suit", "shalwar", "kameez", "dress", "lehenga", "shawl", "shoes", "joota", "khussa", "chappal", "shirt", "jeans", "fabric", "chiffon", "silk"],
    "Electronics": ["laptop", "phone", "smartphone", "mobile", "earbuds", "headphones", "charger", "power bank", "smartwatch", "tv", "led", "tablet", "inverter", "ac", "air conditioner"],
    "Home & Living": ["bedsheet", "comforter", "quilt", "cushion", "dinner set", "kitchen", "curtains", "carpet", "sofa", "lamp", "water dispenser"],
    "Beauty & Personal Care": ["perfume", "fragrance", "lipstick", "cream", "serum", "face wash", "shampoo", "makeup", "lotion", "attar", "sunblock"],
    "Groceries & Essentials": ["tea", "chai", "danedar", "rice", "oil", "ghee", "flour", "atta", "spice", "masala", "milk", "dry fruit", "dates", "khajoor"],
}


class QueryUnderstandingEngine:
    """
    Parses natural language e-commerce search queries in English, Urdu, and Roman Urdu.
    Extracts structured intent, cleans text, and maps colloquial Pakistani expressions.
    """
    def __init__(self):
        pass

    def parse_price(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Extracts minimum and maximum price constraints from text.
        Handles:
        - '20 hazaar' -> 20,000
        - '1.5 lac' / '1.5 lakh' -> 150,000
        - 'under 5000' / 'below 3000' / '5000 tak' / '5000 se kam'
        - 'between 2000 and 5000' / '2000 se 5000'
        - '5k' -> 5,000
        """
        text_lower = text.lower()
        min_price = None
        max_price = None
        
        # 1. Look for range: X se Y tak / between X and Y
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*(k|hazaar|hazar|lac|lakh)?\s*(?:se|to|-|and)\s*(\d+(?:\.\d+)?)\s*(k|hazaar|hazar|lac|lakh)?', text_lower)
        if range_match:
            val1, unit1, val2, unit2 = range_match.groups()
            min_price = self._convert_value_unit(float(val1), unit1 or unit2)
            max_price = self._convert_value_unit(float(val2), unit2 or unit1)
            return min_price, max_price

        # 2. Look for max price: under X / below X / X tak / X se kam / max X / X ke andar
        max_match = re.search(r'(?:under|below|less than|max|maximum|upto|up to)\s*(?:rs\.?|pkr)?\s*(\d+(?:\.\d+)?)\s*(k|hazaar|hazar|lac|lakh)?', text_lower)
        if not max_match:
            max_match = re.search(r'(\d+(?:\.\d+)?)\s*(k|hazaar|hazar|lac|lakh)?\s*(?:ke\s+|k\s+)?(?:tak|se kam|budget|maximum|andar)', text_lower)
            
        if max_match:
            val, unit = max_match.groups()
            max_price = self._convert_value_unit(float(val), unit)
            return None, max_price
            
        # 3. Look for min price: above X / over X / X se zyada / min X
        min_match = re.search(r'(?:above|over|more than|min|minimum)\s*(?:rs\.?|pkr)?\s*(\d+(?:\.\d+)?)\s*(k|hazaar|hazar|lac|lakh)?', text_lower)
        if not min_match:
            min_match = re.search(r'(\d+(?:\.\d+)?)\s*(k|hazaar|hazar|lac|lakh)?\s*(?:se zyada|se ooper)', text_lower)
            
        if min_match:
            val, unit = min_match.groups()
            min_price = self._convert_value_unit(float(val), unit)
            return min_price, None

        return None, None

    def _convert_value_unit(self, val: float, unit: Optional[str]) -> float:
        """Converts colloquial unit multipliers into PKR."""
        if not unit:
            return val
        unit = unit.lower()
        if unit in ["k"]:
            # If val is already in hundreds/thousands (e.g. 1000, 5000), 'k' is the Roman Urdu preposition 'ke' (of), NOT 1,000!
            if val >= 500:
                return val
            return val * 1_000
        elif unit in ["hazaar", "hazar", "thousand"]:
            if val >= 500:
                return val
            return val * 1_000
        elif unit in ["lac", "lakh"]:
            return val * 100_000
        return val

    def extract_attributes(self, text: str) -> Dict[str, Any]:
        """Extracts colour, occasion, gender, category, and normalized query."""
        text_lower = text.lower()
        tokens = re.findall(r'\b\w+\b', text_lower)
        
        extracted_color = None
        for tok in tokens:
            if tok in COLOR_MAPPINGS:
                extracted_color = COLOR_MAPPINGS[tok]
                break
                
        extracted_occasion = None
        for tok in tokens:
            if tok in OCCASION_MAPPINGS:
                extracted_occasion = OCCASION_MAPPINGS[tok]
                break
                
        extracted_target = None
        for tok in tokens:
            if tok in TARGET_MAPPINGS:
                extracted_target = TARGET_MAPPINGS[tok]
                break
                
        # Inferred category
        inferred_category = None
        for cat, kw_list in CATEGORY_KEYWORDS.items():
            for kw in kw_list:
                if kw in text_lower:
                    inferred_category = cat
                    break
            if inferred_category:
                break
                
        # Price extraction first so numeric constraints don't pollute lexical query
        min_p, max_p = self.parse_price(text)

        # Expanded normalized tokens for search matching (comprehensive conversational & Roman Urdu stopwords)
        FILLER_WORDS = {
            "dikhao", "dikhayein", "dikhaye", "chahiye", "mil", "sakta", "hai", "hain", "kuch", 
            "mujhe", "humein", "wali", "wale", "wala", "plz", "please", "batao", "batayein", 
            "koi", "ka", "ki", "ke", "k", "liye", "aur", "mein", "mai", "me", "budget", 
            "khareedny", "khareedna", "khareedne", "kharidna", "lena", "lene", "chahye", "andar", 
            "se", "tak", "under", "below", "above", "rs", "pkr", "hazaar", "hazar", "lac", "lakh"
        }
        
        expanded_terms = []
        for tok in tokens:
            # If token is numeric (price/budget), do not pollute product lexical query
            if tok.isdigit():
                val = float(tok)
                if (max_p and val == max_p) or (min_p and val == min_p) or val >= 100:
                    continue
            if tok in ROMAN_URDU_SYNONYMS:
                expanded_terms.append(ROMAN_URDU_SYNONYMS[tok])
            elif tok not in FILLER_WORDS:
                expanded_terms.append(tok)
                
        if not expanded_terms:
            expanded_terms = [ROMAN_URDU_SYNONYMS.get(t, t) for t in tokens if not t.isdigit()]
            
        clean_search_query = " ".join(expanded_terms).strip()
        if not clean_search_query:
            clean_search_query = text
        
        return {
            "original_query": text,
            "clean_query": clean_search_query,
            "inferred_category": inferred_category,
            "color": extracted_color,
            "occasion": extracted_occasion,
            "target": extracted_target,
            "min_price": min_p,
            "max_price": max_p
        }
