"""
query_understanding.py — pulls structured filters (city, budget, bedrooms,
purpose, property_type) out of a free-text query with regex/keyword
matching, so the StructuredRetriever can build a precise SQL WHERE clause
instead of guessing. Simple by design — a production system would use an
LLM function-call / slot-filling step here instead.
"""
import re

CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad"]
PROPERTY_TYPES = ["House", "Flat", "Upper Portion", "Lower Portion", "Room", "Farm House", "Penthouse"]


def extract_filters(query: str) -> dict:
    q = query
    ql = query.lower()
    filters = {}

    for c in CITIES:
        if c.lower() in ql:
            filters["city"] = c
            break

    for pt in PROPERTY_TYPES:
        if pt.lower() in ql:
            filters["property_type"] = pt
            break

    if "rent" in ql:
        filters["purpose"] = "For Rent"
    elif "sale" in ql or "buy" in ql:
        filters["purpose"] = "For Sale"

    bed_match = re.search(r"(\d+)\s*(-|\s)?bed", ql)
    if bed_match:
        filters["bedrooms"] = int(bed_match.group(1))

    # budget: "under 8 million", "under 8m", "below 20 lac", "max price 5000000"
    money_match = re.search(r"(under|below|less than|max(?:imum)?(?: price)?(?: of)?)\s*(?:pkr|rs\.?)?\s*([\d,\.]+)\s*(m|million|lac|lakh|k|thousand|crore)?", ql)
    if money_match:
        val = float(money_match.group(2).replace(",", ""))
        unit = money_match.group(3)
        if unit in ("m", "million"):
            val *= 1_000_000
        elif unit in ("lac", "lakh"):
            val *= 100_000
        elif unit == "crore":
            val *= 10_000_000
        elif unit in ("k", "thousand"):
            val *= 1_000
        filters["max_price"] = val

    pid_match = re.search(r"propert(?:y|ies)\s*(?:number|no\.?|#)?\s*(\d+)", ql)
    if pid_match:
        filters["property_id"] = int(pid_match.group(1))

    return filters
