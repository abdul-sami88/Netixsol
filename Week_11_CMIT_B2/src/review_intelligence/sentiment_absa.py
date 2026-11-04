"""
Multilingual Sentiment & Aspect-Based Sentiment Analysis (ABSA) Engine
Implements Task 4:
- Multilingual Sentiment Classification (English, Roman Urdu, Urdu Script)
- Aspect-Based Sentiment Analysis across 6 core retail dimensions:
  1. Quality
  2. Price / Value
  3. Delivery / Fulfilment
  4. Size & Fit
  5. Packaging
  6. Seller Behaviour
- Auto-generated "What Customers Say" executive summary per product
"""

import re
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd


# Multilingual lexicon for sentiment and aspect extraction
ASPECT_KEYWORDS = {
    "quality": [
        "quality", "kapra", "fabric", "material", "durability", "stitching", "embroidery", "kam",
        "build", "screen", "camera", "battery", "sound", "awaz", "taste", "zaika", "fragrance", "khushbu"
    ],
    "price": [
        "price", "paisa", "rupees", "rate", "cost", "value", "sasta", "sasti", "mehanga", "mehangi",
        "expensive", "affordable", "worth", "discount", "offer", "paisa wasool", "overpriced"
    ],
    "delivery": [
        "delivery", "shipping", "courier", "rider", "tcs", "leopards", "time", "late", "delay", "der",
        "fast", "jaldi", "arrived", "received", "days", "din", "dispatch"
    ],
    "size_fit": [
        "size", "fit", "fitting", "chhota", "chhoti", "bara", "bari", "loose", "tight", "tang", "khula",
        "length", "waist", "collar", "chest", "chart"
    ],
    "packaging": [
        "packaging", "packing", "box", "dabba", "bubble wrap", "seal", "pack", "broken", "damaged",
        "kharab", "toota", "secure"
    ],
    "seller_behaviour": [
        "seller", "dukaandar", "store", "vendor", "response", "reply", "cooperative", "rude", "rawaiya",
        "fake", "original", "asli", "nakli", "fraud", "dhoka", "scam"
    ]
}

POSITIVE_WORDS = [
    # English
    "good", "great", "excellent", "best", "perfect", "amazing", "love", "awesome", "nice", "durable",
    "fast", "satisfied", "worth", "original", "authentic", "beautiful", "smooth", "high quality",
    # Roman Urdu
    "acha", "achi", "achha", "achhi", "bohot acha", "zabardast", "umda", "kamaal", "behtareen", "pyara",
    "pyari", "khubsurat", "khoobsurat", "pasand", "paisa wasool", "asli", "mazboot", "jaldi aya", "theek"
]

NEGATIVE_WORDS = [
    # English
    "bad", "terrible", "worst", "poor", "horrible", "damaged", "broken", "fake", "delayed", "late",
    "useless", "waste", "disappointed", "slow", "defective", "cheap", "overpriced", "flimsy",
    # Roman Urdu
    "kharab", "fazool", "bekaar", "bekar", "ghatia", "ganda", "naqis", "toota", "chhota", "tight",
    "der se aya", "late delivery", "dhoka", "nakli", "pesa zaya", "farigh", "masla", "kharabi"
]


class ReviewIntelligenceEngine:
    """
    Multilingual Sentiment & Aspect-Based Sentiment Extraction Engine.
    Handles English, Roman Urdu, and Urdu script reviews.
    """
    def __init__(self):
        pass

    def classify_sentiment(self, text: str, rating: Optional[int] = None) -> Tuple[str, float]:
        """
        Classifies review sentiment into Positive, Negative, or Neutral.
        Returns (sentiment_label, confidence_score).
        """
        if not isinstance(text, str):
            return "neutral", 0.5
            
        text_lower = text.lower()
        pos_score = sum(1 for w in POSITIVE_WORDS if w in text_lower)
        neg_score = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
        
        # Consider rating prior if available
        if rating is not None:
            if rating >= 4:
                pos_score += 1.5
            elif rating <= 2:
                neg_score += 1.5
                
        if pos_score > neg_score + 0.5:
            conf = min(0.98, 0.60 + 0.1 * (pos_score - neg_score))
            return "positive", round(conf, 2)
        elif neg_score > pos_score + 0.5:
            conf = min(0.98, 0.60 + 0.1 * (neg_score - pos_score))
            return "negative", round(conf, 2)
        else:
            return "neutral", 0.55

    def extract_aspect_sentiment(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Identifies which aspects are mentioned and assigns aspect-level polarity.
        Returns dict: aspect -> {mentioned: bool, sentiment: 'positive'/'negative'/'neutral', score: float}
        """
        text_lower = text.lower()
        sentences = re.split(r'[,.!?;\n]+', text_lower)
        
        aspect_results = {}
        for aspect, keywords in ASPECT_KEYWORDS.items():
            mentioned = False
            relevant_sentences = []
            for s in sentences:
                if any(kw in s for kw in keywords):
                    mentioned = True
                    relevant_sentences.append(s)
                    
            if not mentioned:
                aspect_results[aspect] = {
                    "mentioned": False,
                    "sentiment": "not_mentioned",
                    "score": 0.0
                }
                continue
                
            # Compute aspect sentiment on the specific sentence window
            context = " ".join(relevant_sentences)
            pos_hits = sum(1 for w in POSITIVE_WORDS if w in context)
            neg_hits = sum(1 for w in NEGATIVE_WORDS if w in context)
            
            if pos_hits > neg_hits:
                sent = "positive"
                score = round(min(1.0, 0.5 + 0.2 * (pos_hits - neg_hits)), 2)
            elif neg_hits > pos_hits:
                sent = "negative"
                score = round(max(-1.0, -0.5 - 0.2 * (neg_hits - pos_hits)), 2)
            else:
                sent = "neutral"
                score = 0.0
                
            aspect_results[aspect] = {
                "mentioned": True,
                "sentiment": sent,
                "score": score
            }
            
        return aspect_results

    def generate_product_summary(self, reviews_df: pd.DataFrame, product_title: str = "") -> str:
        """
        Auto-generates 'What Customers Say' executive summary in Roman Urdu and English:
        E.g. "Zyada tar customers ko kapre ki quality pasand aayi (85%), lekin 30% ne kaha delivery late thi."
        """
        if reviews_df.empty:
            return "Is product par abhi tak customer reviews dastiyab nahi hain."
            
        total = len(reviews_df)
        pos_count = sum(reviews_df["sentiment"] == "positive")
        neg_count = sum(reviews_df["sentiment"] == "negative")
        pos_pct = int(round((pos_count / total) * 100))
        
        # Analyze aspects across all product reviews
        aspect_mentions = {a: {"pos": 0, "neg": 0, "total": 0} for a in ASPECT_KEYWORDS}
        for _, row in reviews_df.iterrows():
            absa = self.extract_aspect_sentiment(str(row["review_text"]))
            for a, data in absa.items():
                if data["mentioned"]:
                    aspect_mentions[a]["total"] += 1
                    if data["sentiment"] == "positive":
                        aspect_mentions[a]["pos"] += 1
                    elif data["sentiment"] == "negative":
                        aspect_mentions[a]["neg"] += 1
                        
        # Synthesize top praises and top complaints
        praises = []
        complaints = []
        
        aspect_names_urdu = {
            "quality": "quality aur material",
            "price": "qeemat aur value",
            "delivery": "delivery speed",
            "size_fit": "size aur fitting",
            "packaging": "packaging",
            "seller_behaviour": "seller ka response"
        }
        
        for a, counts in aspect_mentions.items():
            if counts["total"] >= 1:
                p_rate = counts["pos"] / counts["total"]
                n_rate = counts["neg"] / counts["total"]
                if p_rate > 0.5:
                    praises.append(f"{aspect_names_urdu[a]} ({int(p_rate*100)}% positive)")
                elif n_rate > 0.4:
                    complaints.append(f"{int(n_rate*100)}% ne {aspect_names_urdu[a]} ki shikayat ki")
                    
        summary_lines = []
        summary_lines.append(f"Overall {pos_pct}% customers ne is product ko pasand kiya hai.")
        if praises:
            summary_lines.append(f"Khas taur par {' aur '.join(praises[:2])} ko saraha gaya.")
        if complaints:
            summary_lines.append(f"Lekin {' jabke '.join(complaints[:2])}.")
        else:
            summary_lines.append("Koi numayan shikayat samne nahi aayi.")
            
        return " ".join(summary_lines)

