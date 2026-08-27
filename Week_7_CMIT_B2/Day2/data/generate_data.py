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
    ("What documents are required to buy a property in Pakistan?",
     "You typically need a CNIC copy, proof of funds / bank statement, and (for non-residents) a NICOP or passport. "
     "The seller provides the original title/registry documents, a fard (record of rights), and a no-demand certificate "
     "from the relevant housing authority before transfer."),
    ("How does the installment / payment plan process work?",
     "Most developers require a down payment (typically 10-30% of total price) followed by quarterly or monthly "
     "installments over a fixed period (commonly 2-4 years), with a final possession-linked payment."),
    ("Is property purchase in Pakistan subject to tax?",
     "Yes. Buyers generally pay withholding tax (under Section 236K), stamp duty, and registration fees; sellers pay "
     "capital gains tax (under Section 37) depending on the holding period. Rates vary by filer status and province."),
    ("Can overseas Pakistanis buy property remotely?",
     "Yes, through a Power of Attorney (POA) executed at a Pakistani embassy/consulate, authorizing a representative "
     "in Pakistan to complete the transaction on their behalf."),
    ("What is the difference between a Marla and a Kanal?",
     "1 Kanal = 20 Marla = approximately 605 square yards = about 5,445 square feet. 1 Marla is roughly 272 square feet, "
     "though exact conversions vary slightly by region/province."),
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
    for i, (q, a) in enumerate(FAQ_TEMPLATES, 1):
        rows.append(dict(faq_id=i, question=q, answer=a, category="General"))
    return rows


def gen_descriptions(properties):
    """Synthetic brochure/marketing description text per property - the
    unstructured corpus used for semantic (vector) retrieval."""
    rows = []
    for p in properties:
        amenity_hint = random.sample(AMENITY_POOL, 3)
        purpose_txt = "for sale" if p["purpose"] == "For Sale" else "for rent"
        text = (
            f"This {p['bedrooms']}-bedroom {p['property_type']} is available {purpose_txt} in "
            f"{p['locality']}, {p['city']}. Spread over {p['area']} ({p['area_sqft']} sqft), the property "
            f"features {p['baths']} bathroom(s) and is listed by {p['agency']} through agent {p['agent']}. "
            f"Residents enjoy access to {', '.join(amenity_hint)}. The location offers convenient access to "
            f"schools, hospitals, and main boulevards, making it a great option for families and investors alike. "
            f"Listed on {p['date_added']}."
        )
        rows.append(dict(property_id=p["property_id"], description=text))
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
    write_csv("amenities.csv", gen_amenities(properties))
    write_csv("schools.csv", gen_schools(properties))
    write_csv("hospitals.csv", gen_hospitals(properties))
    write_csv("payment_plans.csv", gen_payment_plans(properties))
    write_csv("developers.csv", gen_developers())
    write_csv("faqs.csv", gen_faqs())
    write_csv("descriptions.csv", gen_descriptions(properties))
