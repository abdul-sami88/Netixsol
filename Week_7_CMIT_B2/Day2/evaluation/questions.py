"""
questions.py — Task 5: 20 evaluation questions.

Each question is labelled with:
  - expected_route: which retrieval path SHOULD answer it ("structured" /
    "semantic" / "hybrid" / "none" for out-of-scope questions)
  - answerable: whether verified data actually exists to answer it (some
    are deliberately unanswerable, to test refusal behaviour instead of
    fabrication — this is the real test of hallucination resistance)
"""

QUESTIONS = [
    # --- structured (SQL-answerable) ---
    {"id": 1, "q": "What is the average price of houses for sale in Lahore?",
     "expected_route": "structured", "answerable": True},
    {"id": 2, "q": "What is the cheapest property currently for sale?",
     "expected_route": "structured", "answerable": True},
    {"id": 3, "q": "What is the most expensive property for sale in Karachi?",
     "expected_route": "structured", "answerable": True},
    {"id": 4, "q": "Show me 2 bedroom flats for rent in Islamabad.",
     "expected_route": "structured", "answerable": True},
    {"id": 5, "q": "Are there any 3 bedroom houses for sale in Karachi under 20 million?",
     "expected_route": "structured", "answerable": False},  # confirmed 0 matches in DB
    {"id": 6, "q": "Who is the listing agent for property number 5?",
     "expected_route": "structured", "answerable": True},
    {"id": 7, "q": "What agency is handling property number 215?",
     "expected_route": "structured", "answerable": True},
    {"id": 8, "q": "How large (in marla) is property number 136?",
     "expected_route": "structured", "answerable": True},
    {"id": 9, "q": "How many bathrooms does property number 193 have?",
     "expected_route": "structured", "answerable": True},
    {"id": 10, "q": "What is the average rent for flats in Rawalpindi?",
     "expected_route": "structured", "answerable": True},

    # --- semantic (vector / FAQ-answerable) ---
    {"id": 11, "q": "What documents are required to buy a property in Pakistan?",
     "expected_route": "semantic", "answerable": True},
    {"id": 12, "q": "How does an installment payment plan typically work?",
     "expected_route": "semantic", "answerable": True},
    {"id": 13, "q": "Is property purchase in Pakistan subject to tax?",
     "expected_route": "semantic", "answerable": True},
    {"id": 14, "q": "Can overseas Pakistanis buy property remotely?",
     "expected_route": "semantic", "answerable": True},
    {"id": 15, "q": "What is the difference between a Marla and a Kanal?",
     "expected_route": "semantic", "answerable": True},
    {"id": 16, "q": "Describe property number 5 and its amenities.",
     "expected_route": "semantic", "answerable": True},

    # --- hybrid ---
    {"id": 17, "q": "Tell me about affordable houses for sale in Faisalabad and what amenities they include.",
     "expected_route": "hybrid", "answerable": True},

    # --- deliberately unanswerable / out-of-scope (should trigger refusal, not hallucination) ---
    {"id": 18, "q": "What is the current State Bank of Pakistan policy interest rate?",
     "expected_route": "none", "answerable": False},
    {"id": 19, "q": "Will property prices in DHA Lahore double in the next 5 years?",
     "expected_route": "none", "answerable": False},
    {"id": 20, "q": "What is the phone number of the agent for property number 999999?",
     "expected_route": "structured", "answerable": False},  # property doesn't exist
]
