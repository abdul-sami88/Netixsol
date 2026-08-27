"""
generate_data.py
-----------------
Generates the full knowledge base for the Zameen.com-style real estate RAG
system. The `properties` table matches the user's exact Postgres schema.
Everything else (amenities, schools, hospitals, payment_plans, developers,
faqs, descriptions/brochures) does not exist in the original Kaggle dump,
so it is synthesized here as realistic dummy data, keyed to real Pakistani
cities/localities so it's consistent with the properties table.

Run: python3 generate_data.py
Outputs CSVs into ./  (this directory)
"""
import random
import csv
import json
from datetime import date, timedelta

random.seed(42)

CITIES = {
    "Lahore": ["DHA Phase 5", "DHA Phase 6", "Bahria Town", "Johar Town", "Gulberg", "Model Town", "Wapda Town"],
    "Karachi": ["DHA Phase 8", "Clifton", "Gulshan-e-Iqbal", "Bahria Town Karachi", "North Nazimabad", "Malir"],
    "Islamabad": ["DHA Islamabad", "Bahria Town Islamabad", "G-13", "F-10", "PWD Housing Scheme", "Gulberg Greens"],
    "Rawalpindi": ["Bahria Town Rawalpindi", "DHA Phase 2 Rawalpindi", "Satellite Town", "Askari 14"],
    "Faisalabad": ["Wapda City", "Susan Road", "Jaranwala Road", "Madina Town", "Eden Valley"],
}

PROPERTY_TYPES = ["House", "Flat", "Upper Portion", "Lower Portion", "Room", "Farm House", "Penthouse"]
PURPOSES = ["For Sale", "For Rent"]
DEVELOPERS = ["Bahria Town Pvt Ltd", "DHA Development Authority", "Emaar Pakistan", "Zedem International",
              "Kohistan Builders", "Al-Jalil Developers", "Park View City Developers", "Nova City Developers"]
AGENCIES = ["Graana Real Estate", "Zameen Estate Hub", "Aiwan-e-Property", "Metro Homes Realty",
            "Prime Estate Consultants", "City Housing Marketing", "Skyline Properties"]
FIRST_NAMES = ["Ahmed", "Bilal", "Sara", "Ayesha", "Usman", "Hassan", "Fatima", "Zainab", "Imran", "Kashif"]
LAST_NAMES = ["Khan", "Malik", "Chaudhry", "Sheikh", "Butt", "Raza", "Iqbal", "Farooq", "Javed", "Aslam"]

AMENITY_POOL = ["24/7 Security", "Gated Community", "Community Park", "Mosque", "Gymnasium", "Swimming Pool",
                "Underground Electricity", "Wide Roads", "Sewerage System", "Backup Generator", "Kids Play Area",
                "BBQ Area", "Club House", "CCTV Surveillance", "Broadband Internet", "Covered Parking",
                "Water Filtration Plant", "Mini Golf Course", "Rooftop Terrace", "Solar Panels"]

SCHOOL_POOL = ["Beaconhouse School System", "The City School", "Roots Millennium Schools", "LGS (Lahore Grammar School)",
               "Bahria Foundation College", "Froebel's International", "Aitchison College", "Army Public School",
               "OPF Girls College", "Divisional Public School"]

HOSPITAL_POOL = ["Shifa International Hospital", "Jinnah Hospital", "South City Hospital", "Doctors Hospital",
                 "Bahria International Hospital", "Chughtai Lab & Hospital", "National Hospital",
                 "Ittefaq Hospital", "Fatima Memorial Hospital", "Kulsum International Hospital"]

FAQ_TEMPLATES = [
    # (category, question, answer, language)
    ("payment", "Down payment kitna hota hai?",
     "Ye property se property vary karta hai, generally 20% se 50% tak. Poori detail property ki payment plan mein mil jayegi.", "urdulish"),
    ("payment", "Kya installment plan available hai har property par?",
     "Zyadatar under-construction aur naye launch properties par installment plans available hain. Ready-to-move properties par aksar full payment required hoti hai.", "urdulish"),
    ("payment", "Installment plan kitne saal ka hota hai?",
     "Zyadatar plans 2 se 4 saal ke tenure mein hote hain, quarterly installments ke saath. Exact tenure property ki payment plan mein confirm ho jata hai.", "urdulish"),
    ("payment", "Kya late installment par penalty lagti hai?",
     "Ye policy developer se developer alag hoti hai. Ye detail mere paas abhi nahi hai, mein confirm kar ke aap ko bata deta hoon.", "urdulish"),
    ("legal", "Kya property clear title hai?",
     "Sab humari listings verified aur clear title ke saath hoti hain, documentation site visit ke waqt dikhayi jati hai.", "urdulish"),
    ("legal", "Kya aap registry aur transfer mein madad karte hain?",
     "Jee haan, humari legal team registry aur transfer ke pure process mein madad karti hai, advisory ke liye koi extra charge nahi hai.", "urdulish"),
    ("legal", "Buy karne ke liye kaun se documents chahiye?",
     "CNIC copy aur proof of funds required hoti hai. Overseas Pakistanis ke liye Power of Attorney ke zariye bhi transaction complete ho sakta hai.", "urdulish"),
    ("legal", "Kya overseas Pakistani property remotely buy kar sakte hain?",
     "Jee bilkul, Power of Attorney embassy ya consulate se attest kara ke Pakistan mein representative ke through poora process ho jata hai.", "urdulish"),
    ("legal", "Property transfer par tax lagta hai kya?",
     "Jee haan, buyer ko withholding tax dena hota hai aur seller ko capital gains tax, rate filer status aur holding period par depend karta hai.", "urdulish"),
    ("amenities", "Community mein kya amenities available hain?",
     "Har property alag hoti hai — kuch mein security, park, gym, aur club house shamil hain. Exact list property ki detail mein confirm ho jayegi.", "urdulish"),
    ("amenities", "Kya property mein swimming pool hai?",
     "Ye har listing par depend karta hai. Mein retrieved data check kar ke bata sakta hoon ke is specific property mein pool available hai ya nahi.", "urdulish"),
    ("location", "School aur hospital kitni door hain?",
     "Zyadatar humari listings mein nearby schools aur hospitals ki distance record hoti hai, 1 se 5 kilometer ke andar. Specific property ke liye mein confirm kar deta hoon.", "urdulish"),
    ("location", "Ye area safe hai kya?",
     "Har location ka apna security setup hota hai — gated societies mein aksar 24/7 security available hoti hai. Mein aap ko exact details retrieved data se bata sakta hoon.", "urdulish"),
    ("investment", "Kya ye acha investment hai?",
     "Mein guaranteed returns ka wada nahi kar sakta, lekin agar historical price trend data available ho to mein woh aap ko share kar deta hoon.", "urdulish"),
    ("investment", "Property ki value future mein barhegi kya?",
     "Ye prediction mere paas nahi hai — hum sirf historical listing data rakhte hain, future price ka andaza nahi laga sakte.", "urdulish"),
    ("builder", "Ye builder acha hai?",
     "Kuch developers ka track record hamare paas record hota hai — jaise active projects aur founding year. Specific developer ke baare mein mein confirm kar ke bata deta hoon.", "urdulish"),
    ("maintenance", "Maintenance charges kitne hain?",
     "Ye har society aur property ke hisaab se different hoti hai. Ye detail mere paas abhi nahi hai, mein confirm kar ke aap ko bata deta hoon.", "urdulish"),
    ("booking", "Site visit kaise book kar sakte hain?",
     "Jee bilkul, mein aap ke liye convenient din aur time check kar ke visit schedule kar deta hoon.", "urdulish"),
    ("booking", "Kya visit cancel ya reschedule ho sakti hai?",
     "Jee haan, koi masla nahi — mein aap ki booking reschedule ya cancel kar sakta hoon, bas mujhe naya time bata dijiye.", "urdulish"),
    ("company", "Aap logo par bharosa kyun karoon?",
     "Ye sawal bilkul jayez hai jab itni bari investment ki baat ho. Humare paas registered properties aur verified listings hain, aur mein aap ko specific details share kar sakta hoon.", "urdulish"),
    ("pricing", "Kya listed price se kam mein deal ho sakta hai?",
     "Listed price se neeche quote karne ke liye human agent ki approval chahiye hoti hai. Mein ye request aage forward kar sakta hoon.", "urdulish"),
]


def rand_date(start_year=2018, end_year=2024):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def gen_properties(n=300):
    rows = []
    loc_id = 1000
    for pid in range(1, n + 1):
        city = random.choice(list(CITIES.keys()))
        locality = random.choice(CITIES[city])
        ptype = random.choice(PROPERTY_TYPES)
        purpose = random.choices(PURPOSES, weights=[0.75, 0.25])[0]
        marla = round(random.choice([3, 5, 7, 8, 10, 12, 15, 20, 25]) * random.uniform(0.9, 1.1), 2)
        sqft = round(marla * 272.25, 2)
        bedrooms = random.choice([1, 2, 3, 4, 5, 6]) if ptype != "Room" else 1
        baths = max(1, bedrooms - random.choice([0, 0, 1]))
        if purpose == "For Sale":
            price = round(marla * random.uniform(1_200_000, 4_500_000) / 5, -3)  # rough PKR pricing per marla scaled
        else:
            price = round(marla * random.uniform(15_000, 45_000), -2)  # monthly rent
        if price < 3_000_000 and purpose == "For Sale":
            bin_ = "Under 3M"
        elif purpose == "For Sale":
            if price < 8_000_000:
                bin_ = "3M - 8M"
            elif price < 20_000_000:
                bin_ = "8M - 20M"
            elif price < 50_000_000:
                bin_ = "20M - 50M"
            else:
                bin_ = "50M+"
        else:
            bin_ = "Rental"
        d = rand_date()
        agency = random.choice(AGENCIES)
        agent = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        lat_base = {"Lahore": 31.5204, "Karachi": 24.8607, "Islamabad": 33.6844,
                    "Rawalpindi": 33.5651, "Faisalabad": 31.4504}[city]
        lon_base = {"Lahore": 74.3587, "Karachi": 67.0011, "Islamabad": 73.0479,
                    "Rawalpindi": 73.0169, "Faisalabad": 73.1350}[city]
        rows.append(dict(
            property_id=pid,
            location_id=loc_id + (pid % 40),
            page_url=f"https://www.zameen.com/Property/{city.lower()}_{locality.lower().replace(' ', '_')}_{pid}.html",
            property_type=ptype,
            price=price,
            price_bin=bin_,
            location=f"{locality}, {city}",
            city=city,
            province_name={"Lahore": "Punjab", "Rawalpindi": "Punjab", "Faisalabad": "Punjab",
                            "Karachi": "Sindh", "Islamabad": "Islamabad Capital Territory"}[city],
            locality=locality,
            latitude=round(lat_base + random.uniform(-0.08, 0.08), 6),
            longitude=round(lon_base + random.uniform(-0.08, 0.08), 6),
            baths=baths,
            area=f"{marla} Marla",
            area_marla=marla,
            area_sqft=sqft,
            purpose=purpose,
            bedrooms=bedrooms,
            date_added=d.isoformat(),
            year=d.year,
            month=d.month,
            day=d.day,
            agency=agency,
            agent=agent,
        ))
    return rows


def gen_locations(properties):
    seen = {}
    for p in properties:
        seen[p["location_id"]] = (p["city"], p["locality"], p["latitude"], p["longitude"], p["province_name"])
    rows = []
    for loc_id, (city, locality, lat, lon, prov) in seen.items():
        rows.append(dict(
            location_id=loc_id, city=city, locality=locality, province_name=prov,
            latitude=lat, longitude=lon,
            popularity_score=round(random.uniform(2.5, 5.0), 1),
            avg_price_per_marla=int(random.uniform(1_500_000, 6_000_000)),
        ))
    return rows


def gen_amenities(properties):
    rows = []
    aid = 1
    for p in properties:
        n = random.randint(4, 9)
        chosen = random.sample(AMENITY_POOL, n)
        for a in chosen:
            rows.append(dict(amenity_id=aid, property_id=p["property_id"], amenity_name=a))
            aid += 1
    return rows


def gen_schools(properties):
    rows = []
    sid = 1
    for loc_id in {p["location_id"] for p in properties}:
        for s in random.sample(SCHOOL_POOL, random.randint(1, 3)):
            rows.append(dict(school_id=sid, location_id=loc_id, school_name=s,
                              distance_km=round(random.uniform(0.3, 4.5), 1),
                              school_type=random.choice(["Private", "Public", "International"])))
            sid += 1
    return rows


def gen_hospitals(properties):
    rows = []
    hid = 1
    for loc_id in {p["location_id"] for p in properties}:
        for h in random.sample(HOSPITAL_POOL, random.randint(1, 2)):
            rows.append(dict(hospital_id=hid, location_id=loc_id, hospital_name=h,
                              distance_km=round(random.uniform(0.5, 6.0), 1),
                              emergency_services=random.choice([True, False])))
            hid += 1
    return rows


def gen_payment_plans(properties):
    rows = []
    ppid = 1
    for p in properties:
        if p["purpose"] != "For Sale":
            continue
        if random.random() < 0.4:  # only some listings have installment plans
            down_pct = random.choice([10, 15, 20, 25, 30])
            years = random.choice([2, 3, 4])
            installments = years * 4
            down_amt = round(p["price"] * down_pct / 100, -3)
            remaining = p["price"] - down_amt
            per_installment = round(remaining / installments, -2)
            rows.append(dict(
                plan_id=ppid, property_id=p["property_id"], down_payment_pct=down_pct,
                down_payment_amount=down_amt, num_installments=installments,
                installment_amount=per_installment, tenure_years=years,
                developer=random.choice(DEVELOPERS),
            ))
            ppid += 1
    return rows


def gen_developers():
    rows = []
    for i, d in enumerate(DEVELOPERS, 1):
        rows.append(dict(
            developer_id=i, developer_name=d,
            founded_year=random.randint(1985, 2015),
            active_projects=random.randint(2, 12),
            reputation_score=round(random.uniform(3.2, 4.9), 1),
            hq_city=random.choice(list(CITIES.keys())),
        ))
    return rows


def gen_faqs():
    rows = []
    for i, (category, q, a, lang) in enumerate(FAQ_TEMPLATES, 1):
        rows.append(dict(faq_id=f"faq_{i:03d}", category=category, question=q, answer=a, language=lang))
    return rows


DESC_ADJECTIVES = ["Modern", "Luxury", "Elegant", "Spacious", "Charming", "Contemporary", "Well-maintained"]
DESC_TYPE_NOUN = {
    "House": "Bungalow", "Flat": "Apartment", "Upper Portion": "Upper Portion",
    "Lower Portion": "Lower Portion", "Room": "Room", "Farm House": "Farm House",
    "Penthouse": "Penthouse",
}
DESC_SECOND_SENTENCE = [
    "Freshly built with contemporary finishes, located close to main boulevards and markets.",
    "Located within a gated community with dedicated security and well-planned streets.",
    "Corner plot design allows extra sunlight and cross-ventilation throughout the home.",
    "Situated in a quiet residential block, ideal for families seeking a peaceful environment.",
    "Recently renovated with modern fittings and ample natural light in every room.",
]
DESC_CLOSING = [
    "Ideal for a small to mid-size family looking for a ready-to-move residential option.",
    "Full amenities access is available within walking distance of the property.",
    "A great pick for investors seeking a well-located, well-maintained property.",
    "Suitable for both end-users and investors given its location and condition.",
    "Close proximity to schools, hospitals, and commercial areas adds to its convenience.",
]


def gen_descriptions(properties, amenities_by_property):
    """Synthetic brochure/marketing description text per property, formatted
    as retrieval-ready chunks: {id, property_id, text}."""
    random.seed(11)
    rows = []
    for p in properties:
        adj = random.choice(DESC_ADJECTIVES)
        noun = DESC_TYPE_NOUN.get(p["property_type"], p["property_type"])
        second = random.choice(DESC_SECOND_SENTENCE)
        closing = random.choice(DESC_CLOSING)
        amen = amenities_by_property.get(p["property_id"], [])
        amen_sentence = f" Amenities include {', '.join(amen[:3])}." if amen else ""
        text = (
            f"{adj} {p['bedrooms']}-Bed {noun} in {p['locality']}, {p['city']}. "
            f"{second}{amen_sentence} {closing}"
        )
        rows.append(dict(id=f"desc_prop_{p['property_id']:03d}", property_id=p["property_id"], text=text))
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


if __name__ == "__main__":
    properties = gen_properties(300)
    write_csv("properties.csv", properties)
    write_csv("locations.csv", gen_locations(properties))
    amenities = gen_amenities(properties)
    write_csv("amenities.csv", amenities)
    write_csv("schools.csv", gen_schools(properties))
    write_csv("hospitals.csv", gen_hospitals(properties))
    write_csv("payment_plans.csv", gen_payment_plans(properties))
    write_csv("developers.csv", gen_developers())
    write_csv("faqs.csv", gen_faqs())
    amenities_by_property = {}
    for a in amenities:
        amenities_by_property.setdefault(a["property_id"], []).append(a["amenity_name"])
    write_csv("descriptions.csv", gen_descriptions(properties, amenities_by_property))
