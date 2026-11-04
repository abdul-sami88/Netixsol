"""
ShopKaro E-Commerce Dataset Generator
Generates realistic e-commerce data tailored to the Pakistani market context:
- 50,000 products across Pakistani categories & brands (PKR prices)
- 2-year calendar with Pakistani festivals (Ramadan, Eid ul-Fitr, Eid ul-Adha, 11.11, Azadi Sale, Blessed Friday)
- 600,000+ user interaction events (view, add_to_cart, purchase)
- Authentic noise: bot traffic, duplicate clicks, runaway crawler sessions
- 6,000+ reviews in English, Roman Urdu, and Urdu script
"""

import os
import random
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

# Set seeds for reproducibility
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. PAKISTANI FESTIVAL CALENDAR (2024 - 2025)
# ---------------------------------------------------------
def generate_calendar() -> pd.DataFrame:
    """Generate daily calendar table with Pakistani festivals & seasonal multipliers."""
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    
    calendar_data = []
    
    # Festival intervals (approximate real moonsighting dates in Pakistan for 2024 & 2025)
    festivals = [
        # 2024
        ("Pakistan Day Sale", datetime.date(2024, 3, 20), datetime.date(2024, 3, 24), 1.6, "all"),
        ("Ramadan Season", datetime.date(2024, 3, 11), datetime.date(2024, 4, 8), 1.8, "groceries,fashion"),
        ("Chaand Raat & Eid ul-Fitr", datetime.date(2024, 4, 5), datetime.date(2024, 4, 13), 2.8, "fashion,beauty,home"),
        ("Eid ul-Adha (Bakra Eid)", datetime.date(2024, 6, 12), datetime.date(2024, 6, 20), 2.2, "home,appliances,groceries"),
        ("Back to School", datetime.date(2024, 8, 15), datetime.date(2024, 9, 5), 1.5, "stationery,electronics"),
        ("Azadi Sale (14 August)", datetime.date(2024, 8, 10), datetime.date(2024, 8, 15), 1.7, "fashion,electronics"),
        ("11.11 Mega Sale", datetime.date(2024, 11, 8), datetime.date(2024, 11, 14), 3.5, "all"),
        ("Blessed Friday Sale", datetime.date(2024, 11, 25), datetime.date(2024, 11, 30), 2.4, "electronics,fashion"),
        ("Winter Festive & Wedding Season", datetime.date(2024, 12, 15), datetime.date(2024, 12, 31), 1.6, "fashion,home"),
        
        # 2025
        ("Ramadan Season", datetime.date(2025, 2, 28), datetime.date(2025, 3, 29), 1.8, "groceries,fashion"),
        ("Pakistan Day Sale", datetime.date(2025, 3, 21), datetime.date(2025, 3, 24), 1.6, "all"),
        ("Chaand Raat & Eid ul-Fitr", datetime.date(2025, 3, 26), datetime.date(2025, 4, 3), 2.9, "fashion,beauty,home"),
        ("Eid ul-Adha (Bakra Eid)", datetime.date(2025, 6, 2), datetime.date(2025, 6, 9), 2.2, "home,appliances,groceries"),
        ("Azadi Sale (14 August)", datetime.date(2025, 8, 10), datetime.date(2025, 8, 15), 1.7, "fashion,electronics"),
        ("Back to School", datetime.date(2025, 8, 15), datetime.date(2025, 9, 5), 1.5, "stationery,electronics"),
        ("11.11 Mega Sale", datetime.date(2025, 11, 8), datetime.date(2025, 11, 14), 3.6, "all"),
        ("Blessed Friday Sale", datetime.date(2025, 11, 24), datetime.date(2025, 11, 30), 2.5, "electronics,fashion"),
        ("Winter Festive & Wedding Season", datetime.date(2025, 12, 15), datetime.date(2025, 12, 31), 1.6, "fashion,home"),
    ]
    
    for dt in dates:
        d = dt.date()
        is_fest = False
        fest_name = "Regular Day"
        multiplier = 1.0
        affected_cats = "none"
        
        for name, f_start, f_end, mult, cats in festivals:
            if f_start <= d <= f_end:
                is_fest = True
                fest_name = name
                multiplier = max(multiplier, mult)
                affected_cats = cats
                break
                
        calendar_data.append({
            "date": str(d),
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "day_of_week": d.strftime("%A"),
            "is_weekend": d.weekday() in [5, 6],
            "is_festival": is_fest,
            "festival_name": fest_name,
            "demand_multiplier": multiplier,
            "affected_categories": affected_cats
        })
        
    df_cal = pd.DataFrame(calendar_data)
    df_cal.to_csv(os.path.join(OUTPUT_DIR, "calendar.csv"), index=False)
    print(f"Generated calendar: {len(df_cal)} days (2024-2025).")
    return df_cal


# ---------------------------------------------------------
# 2. PRODUCT CATALOGUE (50,000 PRODUCTS)
# ---------------------------------------------------------
CATEGORIES = {
    "Fashion": {
        "subcategories": [
            "Women's Unstitched Lawn", "Women's Ready to Wear", "Men's Shalwar Kameez",
            "Men's Kurta & Waistcoats", "Formal Chiffon & Silk", "Shawls & Winter Wear",
            "Footwear & Khussa", "Handbags & Clutches"
        ],
        "brands": [
            "Khaadi", "Gul Ahmed", "Sana Safinaz", "Junaid Jamshed", "Alkaram Studio",
            "Sapphire", "Nishat Linen", "Maria.B", "Bonanza Satrangi", "Bareeze",
            "Asim Jofa", "Outfitters", "Charcoal", "Service", "Bata Pakistan"
        ],
        "price_range": (1200, 28000),
        "weight": 0.35
    },
    "Electronics": {
        "subcategories": [
            "Smartphones", "Feature Phones", "Smartwatches & Fitness Bands",
            "TWS Wireless Earbuds", "Power Banks & Chargers", "Inverter Air Conditioners",
            "LED TVs & Smart Displays", "Laptops & Tablets", "Solar Inverters & Batteries"
        ],
        "brands": [
            "Infinix", "Xiaomi", "Samsung Pakistan", "Tecno", "Realme",
            "Haier Pakistan", "Dawlance", "Gree", "Orient", "Audionic",
            "Ronin", "Faster", "EcoStar", "Inverex", "Crown Micro"
        ],
        "price_range": (850, 245000),
        "weight": 0.25
    },
    "Home & Living": {
        "subcategories": [
            "Cotton Bed Sheet Sets", "Comforters & Quilts", "Prayer Rugs (Janamaz)",
            "Kitchen & Non-Stick Cookware", "Dinner Sets & Cutlery", "Water Dispensers & Coolers",
            "Ceiling & Bracket Fans", "Emergency Rechargeable Lights"
        ],
        "brands": [
            "ChenOne", "Habitt", "Pak Fan", "Royal Fans", "Super Asia",
            "Citizen Home", "Sona Bakers", "Diamond Supreme Foam", "Master MoltyFoam"
        ],
        "price_range": (600, 45000),
        "weight": 0.15
    },
    "Beauty & Personal Care": {
        "subcategories": [
            "Halal Skincare & Sunblock", "Organic Hair Oils & Shampoos", "Attar & Non-Alcoholic Perfumes",
            "Lipsticks & Makeup Palettes", "Herbal Face Wash & Ubtan", "Grooming & Trimmers"
        ],
        "brands": [
            "Saeed Ghani", "Hemani Herbal", "Rivaj UK", "J. Fragrances", "Golden Rose",
            "Vince Care", "BioCos", "Medora of London", "WB by Hemani"
        ],
        "price_range": (250, 14000),
        "weight": 0.13
    },
    "Groceries & Essentials": {
        "subcategories": [
            "Super Kernel Basmati Rice", "Cooking Oil & Desi Ghee", "Biryani & Curry Recipe Masalas",
            "Chai & Danedar Black Tea", "Daal, Pulses & Lentils", "Dry Fruits & Pine Nuts (Chilgoza)",
            "Honey & Jams", "Packaged Milk & Dairy"
        ],
        "brands": [
            "Shan Foods", "National Foods", "Tapal Tea", "Vital Tea", "Dalda",
            "Mezan Oil", "Guard Rice", "Olper's", "Nestle Pakistan", "Marhaba"
        ],
        "price_range": (120, 16500),
        "weight": 0.12
    }
}

ADJECTIVES = [
    "Premium", "Deluxe", "Classic", "Original", "Embroidered", "Digital Printed",
    "Smart Dual-Inverter", "Festive Edition", "Limited Eid Edition", "Royal Gold",
    "Heavy Duty", "Pure Organic", "Ultra Fast", "Portable Mini", "Traditional Handcrafted",
    "Summer Lawn", "Winter Velvet", "Noise Cancelling", "Energy Saving", "Signature"
]

def generate_catalogue(n_products: int = 50000) -> pd.DataFrame:
    """Generate 50,000 realistic Pakistani products."""
    print(f"Generating {n_products} products for ShopKaro...")
    
    categories_list = list(CATEGORIES.keys())
    cat_weights = [CATEGORIES[c]["weight"] for c in categories_list]
    
    # Assign department counts according to weights
    dept_assignments = np.random.choice(categories_list, size=n_products, p=cat_weights)
    
    products = []
    
    for i in range(n_products):
        pid = f"PROD-{i+1:05d}"
        cat = dept_assignments[i]
        cat_info = CATEGORIES[cat]
        
        subcat = random.choice(cat_info["subcategories"])
        brand = random.choice(cat_info["brands"])
        adj = random.choice(ADJECTIVES)
        
        # Product title in e-commerce style
        title = f"{brand} {adj} {subcat}"
        if cat == "Fashion":
            title += f" - {random.choice(['Volume 1', 'Volume 2', 'Eid Collection', 'Festive Series', 'Stitched', 'Unstitched 3-Pc'])}"
        elif cat == "Electronics":
            title += f" - {random.choice(['Official Warranty', 'PTA Approved', 'Fast Charge', 'Pro Max Edition', 'Series X'])}"
            
        p_min, p_max = cat_info["price_range"]
        # Log-uniform distribution for prices to reflect real market spread
        price_pkr = int(np.exp(np.random.uniform(np.log(p_min), np.log(p_max))))
        # Round price cleanly to Pakistani market psychological endings (e.g. 990, 1450, 4999)
        if price_pkr > 5000:
            price_pkr = (price_pkr // 500) * 500 - 1
        elif price_pkr > 1000:
            price_pkr = (price_pkr // 100) * 100 - 1
        else:
            price_pkr = (price_pkr // 10) * 10 - 1
        price_pkr = max(99, price_pkr)
        
        # Cost price (margins: fashion 45%, electronics 12%, beauty 50%, groceries 15%, home 35%)
        margin_map = {"Fashion": 0.45, "Electronics": 0.12, "Beauty & Personal Care": 0.50, "Groceries & Essentials": 0.15, "Home & Living": 0.35}
        margin = margin_map.get(cat, 0.3)
        cost_pkr = int(price_pkr * (1.0 - margin * np.random.uniform(0.8, 1.2)))
        
        # Initial inventory stock
        stock = int(np.random.choice([0, 5, 15, 45, 120, 350, 800], p=[0.05, 0.10, 0.25, 0.30, 0.18, 0.08, 0.04]))
        
        # Description
        desc = (
            f"Original {title} by {brand}. Designed for top performance and genuine quality. "
            f"Guaranteed official authentic stock for nationwide delivery across Pakistan. "
            f"Category: {cat} > {subcat}."
        )
        
        # Price tier band
        if price_pkr < 1500:
            price_tier = "Budget"
        elif price_pkr < 6000:
            price_tier = "Mid-Range"
        elif price_pkr < 25000:
            price_tier = "Premium"
        else:
            price_tier = "Luxury"
            
        products.append({
            "product_id": pid,
            "sku": f"SK-{brand[:3].upper()}-{subcat[:3].upper()}-{i+1:05d}",
            "title": title,
            "category": cat,
            "subcategory": subcat,
            "brand": brand,
            "price_pkr": price_pkr,
            "cost_pkr": cost_pkr,
            "price_tier": price_tier,
            "stock_quantity": stock,
            "description": desc,
            "rating_avg": round(float(np.random.normal(4.2, 0.5)), 1),
            "is_active": True
        })
        
    df_prod = pd.DataFrame(products)
    # Clip ratings to 1.0 - 5.0
    df_prod["rating_avg"] = df_prod["rating_avg"].clip(1.0, 5.0)
    
    df_prod.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    print(f"Product catalogue generated: {len(df_prod)} items.")
    return df_prod


# ---------------------------------------------------------
# 3. USERS (25,000 ACTIVE CUSTOMERS)
# ---------------------------------------------------------
PAKISTANI_CITIES = [
    ("Karachi", 0.34), ("Lahore", 0.28), ("Islamabad", 0.11), ("Rawalpindi", 0.07),
    ("Faisalabad", 0.06), ("Multan", 0.04), ("Peshawar", 0.04), ("Sialkot", 0.03),
    ("Gujranwala", 0.02), ("Quetta", 0.01)
]

FIRST_NAMES = [
    "Muhammad", "Ali", "Ahmed", "Fatima", "Ayesha", "Zainab", "Hamza", "Bilal",
    "Usman", "Sara", "Hassan", "Hussain", "Zubair", "Mariam", "Sana", "Sadia",
    "Tariq", "Imran", "Kashif", "Nadia", "Farhan", "Hira", "Mahnoor", "Saad"
]
LAST_NAMES = [
    "Khan", "Malik", "Chaudhry", "Sheikh", "Bhatti", "Qureshi", "Abbasi", "Siddiqui",
    "Raza", "Shah", "Ansari", "Mirza", "Farooqi", "Javed", "Akram", "Butt"
]

def generate_users(n_users: int = 25000) -> pd.DataFrame:
    """Generate 25,000 realistic Pakistani customer profiles."""
    print(f"Generating {n_users} user profiles...")
    
    cities, city_probs = zip(*PAKISTANI_CITIES)
    assigned_cities = np.random.choice(cities, size=n_users, p=city_probs)
    
    # Registration dates spread across 2023 - 2025
    start_ts = datetime.datetime(2023, 1, 1).timestamp()
    end_ts = datetime.datetime(2025, 10, 1).timestamp()
    reg_timestamps = np.random.uniform(start_ts, end_ts, size=n_users)
    
    payment_methods = ["Cash on Delivery (COD)", "JazzCash", "EasyPaisa", "Bank Transfer / Card"]
    pay_probs = [0.68, 0.16, 0.10, 0.06]
    assigned_payments = np.random.choice(payment_methods, size=n_users, p=pay_probs)
    
    users = []
    for i in range(n_users):
        uid = f"USR-{i+1:05d}"
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        reg_dt = datetime.datetime.fromtimestamp(reg_timestamps[i]).strftime("%Y-%m-%d %H:%M:%S")
        
        users.append({
            "user_id": uid,
            "full_name": f"{fn} {ln}",
            "city": assigned_cities[i],
            "registration_date": reg_dt,
            "preferred_payment": assigned_payments[i],
            "phone_prefix": random.choice(["0300", "0301", "0312", "0321", "0333", "0345"]),
            "device_preference": np.random.choice(["Android Mobile", "iOS Mobile", "Desktop/Web"], p=[0.78, 0.14, 0.08])
        })
        
    df_users = pd.DataFrame(users)
    df_users.to_csv(os.path.join(OUTPUT_DIR, "users.csv"), index=False)
    print(f"Users generated: {len(df_users)} customers.")
    return df_users


# ---------------------------------------------------------
# 4. USER INTERACTIONS (600,000+ EVENTS)
# ---------------------------------------------------------
def generate_events(
    df_prod: pd.DataFrame,
    df_users: pd.DataFrame,
    df_cal: pd.DataFrame,
    n_events: int = 650000
) -> pd.DataFrame:
    """
    Generate 650,000+ realistic e-commerce interaction events.
    Includes:
    - View, Cart, Purchase funnels
    - Power-law item popularity (Pareto distribution)
    - Festival spikes based on calendar demand multipliers
    - Synthetic anomalies (Bots, duplicate clicks, 1,000+ click outlier sessions)
    """
    print(f"Simulating {n_events} raw events with Pakistani festival temporal dynamics...")
    
    prod_ids = df_prod["product_id"].values
    n_prods = len(prod_ids)
    
    # 1. Pareto item popularity distribution (alpha = 1.3)
    # 20% of products get ~80% of views
    popularity_weights = 1.0 / np.power(np.arange(1, n_prods + 1), 1.25)
    popularity_weights /= popularity_weights.sum()
    
    user_ids = df_users["user_id"].values
    n_u = len(user_ids)
    # User activity distribution (some active power shoppers, many casual visitors)
    user_weights = 1.0 / np.power(np.arange(1, n_u + 1), 0.8)
    user_weights /= user_weights.sum()
    
    # Calendar date sampling with festival weighting
    date_weights = df_cal["demand_multiplier"].values.copy()
    date_weights /= date_weights.sum()
    sampled_dates = np.random.choice(df_cal["date"].values, size=n_events, p=date_weights)
    
    # Sample items according to popularity
    sampled_items = np.random.choice(prod_ids, size=n_events, p=popularity_weights)
    
    # Sample users according to user weights
    sampled_users = np.random.choice(user_ids, size=n_events, p=user_weights)
    
    # Event types: View (75%), Add to Cart (18%), Purchase (7%)
    event_types = np.random.choice(
        ["view", "add_to_cart", "purchase"],
        size=n_events,
        p=[0.75, 0.18, 0.07]
    )
    
    # Generate realistic timestamps across the 24 hours of each sampled date
    # In Pakistan, e-commerce has major nighttime activity, especially during Ramadan after Taraweeh (10 PM - 2 AM)
    hour_probs = np.array([
        0.03, 0.02, 0.015, 0.01, 0.005, 0.005, 0.01, 0.02, 0.035, 0.05, 0.06, 0.065, # 00-11
        0.07, 0.065, 0.06, 0.055, 0.055, 0.06, 0.07, 0.075, 0.08, 0.085, 0.09, 0.06   # 12-23
    ])
    hour_probs /= hour_probs.sum()
    sampled_hours = np.random.choice(24, size=n_events, p=hour_probs)
    sampled_minutes = np.random.choice(60, size=n_events)
    sampled_seconds = np.random.choice(60, size=n_events)
    
    timestamps = [
        f"{d} {h:02d}:{m:02d}:{s:02d}"
        for d, h, m, s in zip(sampled_dates, sampled_hours, sampled_minutes, sampled_seconds)
    ]
    
    user_agents = [
        "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; Infinix X6816D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    ]
    sampled_uas = np.random.choice(user_agents, size=n_events, p=[0.55, 0.15, 0.12, 0.18])
    
    df_events = pd.DataFrame({
        "event_id": [f"EVT-{i+1:08d}" for i in range(n_events)],
        "timestamp": timestamps,
        "user_id": sampled_users,
        "product_id": sampled_items,
        "event_type": event_types,
        "user_agent": sampled_uas
    })
    
    # ----------------------------------------------------
    # INJECT REAL-WORLD NOISE (As specified in Task 1):
    # 1. Bots (Scrapers with Python-urllib / Selenium or 200+ fast hits)
    # 2. Duplicate clicks (double-clicks at identical timestamp)
    # 3. Outlier session with 1,000+ clicks
    # ----------------------------------------------------
    print("Injecting synthetic bot traffic, duplicate clicks, and runaway sessions...")
    
    # 1. Duplicate events (1,500 duplicate clicks)
    dup_sample = df_events.iloc[:1500].copy()
    dup_sample["event_id"] = [f"EVT-DUP-{i+1:05d}" for i in range(1500)]
    
    # 2. Bot traffic (3,000 bot hits from 3 bot accounts with bot user-agent)
    bot_users = ["USR-BOT-01", "USR-BOT-02", "USR-BOT-03"]
    bot_uas = ["Scrapy/2.9.0 (+https://scrapy.org)", "python-requests/2.31.0", "AhrefsBot/7.0"]
    bot_events = []
    bot_base_ts = datetime.datetime(2024, 7, 10, 14, 0, 0)
    for bi in range(3000):
        bot_events.append({
            "event_id": f"EVT-BOT-{bi+1:05d}",
            "timestamp": (bot_base_ts + datetime.timedelta(seconds=bi // 10)).strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": random.choice(bot_users),
            "product_id": random.choice(prod_ids),
            "event_type": "view",
            "user_agent": random.choice(bot_uas)
        })
    df_bots = pd.DataFrame(bot_events)
    
    # 3. Outlier user session (1,250 consecutive rapid clicks from user USR-RUNAWAY)
    runaway_events = []
    runaway_base_ts = datetime.datetime(2024, 9, 1, 10, 0, 0)
    for ri in range(1250):
        runaway_events.append({
            "event_id": f"EVT-RUNAWAY-{ri+1:05d}",
            "timestamp": (runaway_base_ts + datetime.timedelta(seconds=ri * 2)).strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": "USR-RUNAWAY",
            "product_id": random.choice(prod_ids),
            "event_type": "view",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
    df_runaway = pd.DataFrame(runaway_events)
    
    # Combine everything
    df_all_events = pd.concat([df_events, dup_sample, df_bots, df_runaway], ignore_index=True)
    # Sort chronologically
    df_all_events.sort_values(by="timestamp", inplace=True)
    df_all_events.reset_index(drop=True, inplace=True)
    
    df_all_events.to_csv(os.path.join(OUTPUT_DIR, "events_raw.csv"), index=False)
    print(f"Total raw events generated: {len(df_all_events):,} (including noise).")
    return df_all_events


# ---------------------------------------------------------
# 5. REVIEWS (6,000+ MULTILINGUAL: ENGLISH, ROMAN URDU, URDU)
# ---------------------------------------------------------
ROMAN_URDU_REVIEWS = [
    (5, "Bohot pyara suit hai! Kapra aur embroidery bilkul picture jaisi hai. Eid ke liye perfect hai.", "Roman Urdu"),
    (5, "Alhamdulillah bohot zabardast product hai. Sound quality kamaal hai, delivery Lahore mein 2 din mein aa gayi.", "Roman Urdu"),
    (4, "Kapra acha hai lekin delivery thori late thi. Overall satisfied hoon ShopKaro ki service se.", "Roman Urdu"),
    (4, "Paisa wasool cheez hai! Market se kafi sasta mila aur packing bhi solid thi.", "Roman Urdu"),
    (3, "Product theek hai normal quality ka. Color zara 19-20 hai picture se alag.", "Roman Urdu"),
    (2, "Size chart theek nahi hai. Small order kiya tha lekin medium jaisa fit hai. Exchange process bohot slow hai.", "Roman Urdu"),
    (1, "Bohot ghatiya experience raha. Box phata hua mila aur product defective thi. Return request daali hai.", "Roman Urdu"),
    (5, "11.11 sale mein bohot zabardast discount mila. Original battery backup bohot acha hai.", "Roman Urdu"),
    (4, "Khaadi ka original kurta hai, stitching bohot saaf hai. Shukriya seller!", "Roman Urdu"),
    (2, "Kapray ka rang pehle hi wash mein utar gaya. Expectation se bilkul kam standard hai.", "Roman Urdu"),
    (5, "Inverter AC bohot zabardast cooling kar raha hai. Karachi ki garmi mein sakoon ho gaya.", "Roman Urdu"),
    (3, "Average quality. Shan ka masala toh har ghar ki zaroorat hai, packaging thori behter ho sakti thi.", "Roman Urdu"),
]

URDU_SCRIPT_REVIEWS = [
    (5, "بہت ہی شاندار اور نفیس کوالٹی ہے۔ عید کی مناسبت سے بہترین جوڑا ہے۔", "Urdu"),
    (5, "الحمدللہ بالکل اصل پراڈکٹ ملی ہے۔ اسلام آباد میں دو دن میں ڈلیوری پہنچ گئی۔", "Urdu"),
    (4, "پراڈکٹ بہت اچھی ہے مگر پیکنگ تھوڑی بہتر ہو سکتی تھی۔ مجموعی طور پر مطمئن ہوں۔", "Urdu"),
    (4, "قیمت مناسب ہے اور کوالٹی مارکیٹ سے بہت بہتر ہے۔ شکریہ شاپ کرو۔", "Urdu"),
    (3, "کوالٹی درمیانی ہے، تصویر کے مقابلے میں رنگ تھوڑا مدھم ہے۔", "Urdu"),
    (2, "ڈلیوری بہت تاخیر سے ہوئی۔ کسٹمر سروس نے بھی فوری جواب نہیں دیا۔", "Urdu"),
    (1, "خراب پراڈکٹ موصول ہوئی اور سائز بھی غلط بھیجا گیا۔ انتہائی مایوس کن تجربہ۔", "Urdu"),
    (5, "سیل میں بہت مناسب ریٹ پر مل گیا۔ زبردست کوالٹی اور تیز ترین ڈلیوری۔", "Urdu")
]

ENGLISH_REVIEWS = [
    (5, "Outstanding quality and authentic fabric! Exactly as displayed in the product imagery.", "English"),
    (5, "Great battery life and seamless Bluetooth pairing. Prompt delivery in Karachi.", "English"),
    (4, "Good value for money. Minor stitching imperfections on the collar, but acceptable at this price.", "English"),
    (4, "Fast dispatch and genuine warranty card included. Highly recommended seller.", "English"),
    (3, "Average build quality. The fabric texture is slightly thinner than expected for winter wear.", "English"),
    (2, "Delivery took over 8 days to Faisalabad. The packaging box was damaged upon arrival.", "English"),
    (1, "Completely disappointed. The item stopped working after 3 days. Seeking full refund.", "English"),
    (5, "Best purchase during the 11.11 mega discount festival. Truly high performance device.", "English")
]

def generate_reviews(df_prod: pd.DataFrame, df_users: pd.DataFrame, n_reviews: int = 6000) -> pd.DataFrame:
    """Generate 6,000+ realistic multilingual reviews."""
    print(f"Generating {n_reviews} multilingual customer reviews...")
    
    prod_ids = df_prod["product_id"].values
    user_ids = df_users["user_id"].values
    
    all_templates = (
        ROMAN_URDU_REVIEWS * 4 +   # ~45%
        ENGLISH_REVIEWS * 3 +       # ~35%
        URDU_SCRIPT_REVIEWS * 2     # ~20%
    )
    
    reviews = []
    base_date = datetime.date(2024, 1, 15)
    
    for i in range(n_reviews):
        rating, text_template, lang = random.choice(all_templates)
        
        # Add slight natural variability
        pid = random.choice(prod_ids)
        uid = random.choice(user_ids)
        day_offset = random.randint(0, 680)
        review_dt = base_date + datetime.timedelta(days=day_offset)
        
        sentiment = "positive" if rating >= 4 else ("neutral" if rating == 3 else "negative")
        
        reviews.append({
            "review_id": f"REV-{i+1:06d}",
            "product_id": pid,
            "user_id": uid,
            "rating": rating,
            "review_text": text_template,
            "language": lang,
            "sentiment": sentiment,
            "created_at": review_dt.strftime("%Y-%m-%d")
        })
        
    df_rev = pd.DataFrame(reviews)
    df_rev.to_csv(os.path.join(OUTPUT_DIR, "reviews.csv"), index=False)
    print(f"Reviews generated: {len(df_rev)} multilingual reviews.")
    return df_rev


def main():
    print("="*60)
    print("SHOPKARO DATA FOUNDATION GENERATOR")
    print("Building realistic Pakistani E-Commerce Datasets...")
    print("="*60)
    
    df_cal = generate_calendar()
    df_prod = generate_catalogue(n_products=50000)
    df_users = generate_users(n_users=25000)
    df_events = generate_events(df_prod, df_users, df_cal, n_events=650000)
    df_rev = generate_reviews(df_prod, df_users, n_reviews=6000)
    
    print("\n[SUCCESS] All raw datasets generated in 'data/raw/':")
    print(f" - calendar.csv: {len(df_cal):,} rows")
    print(f" - products.csv: {len(df_prod):,} rows (50,000 PKR products)")
    print(f" - users.csv:    {len(df_users):,} rows")
    print(f" - events_raw.csv: {len(df_all_events if 'df_all_events' in locals() else df_events):,} rows (>600k events)")
    print(f" - reviews.csv:  {len(df_rev):,} rows (Urdu, Roman Urdu, English)")

if __name__ == "__main__":
    main()
