import sqlite3
import json
import random
from database import init_db, get_db_connection

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing tables to avoid duplicate entries
    cursor.execute("DELETE FROM properties")
    cursor.execute("DELETE FROM payment_plans")
    cursor.execute("DELETE FROM agents")
    cursor.execute("DELETE FROM faqs")

    random.seed(42) # Reproducible realistic generator

    cities_data = {
        "Lahore": {
            "areas": ["DHA Phase 6", "DHA Phase 8", "Bahria Town Sector C", "Gulberg III", "Lake City Sector M"],
            "schools": ["LGS Phase 5", "Beaconhouse Defence Campus", "Army Public School", "Bloomfield Hall"],
            "hospitals": ["National Hospital DHA", "Doctors Hospital", "Avenue Hospital", "Shaukat Khanum Annex"]
        },
        "Islamabad": {
            "areas": ["DHA Phase 2", "Gulberg Greens", "E-11/2", "G-13/3", "B-17 Multi Gardens"],
            "schools": ["Roots Millennium", "Headstart School", "Army Public School E-11", "City School Capital"],
            "hospitals": ["Shifa International", "Kulsum International", "Quaid-e-Azam International Hospital"]
        },
        "Karachi": {
            "areas": ["DHA Phase 8", "Bahria Town Precinct 1", "Clifton Block 4", "Scheme 33", "Emaar Crescent Bay"],
            "schools": ["Karachi Grammar School", "CAS School", "Beaconhouse PECHS", "Army Public School Phase 6"],
            "hospitals": ["Aga Khan University Hospital", "South City Hospital", "Ziauddin Hospital Clifton"]
        }
    }

    developers = [
        "DHA Developers",
        "Bahria Town Pvt Ltd",
        "Emaar Pakistan",
        "Imarat Group of Companies",
        "Habib Rafiq (Pvt) Ltd"
    ]

    property_templates = [
        {"type": "House", "size_val": 5, "unit": "Marla", "beds": 3, "baths": 4, "base_price": 18000000},
        {"type": "House", "size_val": 10, "unit": "Marla", "beds": 4, "baths": 5, "base_price": 35000000},
        {"type": "House", "size_val": 1, "unit": "Kanal", "beds": 5, "baths": 6, "base_price": 75000000},
        {"type": "House", "size_val": 2, "unit": "Kanal", "beds": 6, "baths": 7, "base_price": 140000000},
        {"type": "Apartment", "size_val": 1200, "unit": "Sq Ft", "beds": 2, "baths": 2, "base_price": 16000000},
        {"type": "Apartment", "size_val": 1800, "unit": "Sq Ft", "beds": 3, "baths": 3, "base_price": 26000000},
        {"type": "Plot", "size_val": 5, "unit": "Marla", "beds": 0, "baths": 0, "base_price": 8500000},
        {"type": "Plot", "size_val": 10, "unit": "Marla", "beds": 0, "baths": 0, "base_price": 16500000},
        {"type": "Plot", "size_val": 1, "unit": "Kanal", "beds": 0, "baths": 0, "base_price": 32000000},
        {"type": "Commercial", "size_val": 500, "unit": "Sq Ft", "beds": 0, "baths": 1, "base_price": 22000000},
    ]

    all_amenities = [
        "24/7 Security & CCTV", "Gated Community", "Underground Electricity", "Park View",
        "Solar Backup Ready", "Smart Home Automation", "Maid Room", "Covered Car Parking",
        "Swimming Pool Access", "Gymnasium", "Corner Plot", "Main Boulevard Frontage"
    ]

    def format_pkr(price):
        if price >= 10000000:
            crore = price / 10000000
            return f"{crore:.2f}".rstrip('0').rstrip('.') + " Crore"
        else:
            lakh = price / 100000
            return f"{lakh:.1f}".rstrip('0').rstrip('.') + " Lakh"

    properties_count = 0
    for city, city_info in cities_data.items():
        for area in city_info["areas"]:
            # Pick 3 to 4 properties per area to reach 50+ total
            for _ in range(random.randint(3, 4)):
                properties_count += 1
                tmpl = random.choice(property_templates)
                price_variance = random.uniform(0.9, 1.25)
                price = round(tmpl["base_price"] * price_variance, -5)
                
                title = f"{tmpl['size_val']} {tmpl['unit']} Modern {tmpl['type']} in {area}, {city}"
                dev = random.choice(developers)
                purpose = "Rent" if (tmpl['type'] != "Plot" and random.random() < 0.25) else "Sale"
                
                if purpose == "Rent":
                    price = round(price * 0.004, -3) # Realistic rent approx 0.4% monthly value
                    
                price_fmt = format_pkr(price) if purpose == "Sale" else f"{int(price):,} PKR/month"
                amenities_sample = random.sample(all_amenities, random.randint(4, 7))
                schools = random.sample(city_info["schools"], 2)
                hospitals = random.sample(city_info["hospitals"], 2)
                
                desc = (
                    f"Brand new luxury {tmpl['type'].lower()} offered by {dev} located prime position in {area}, {city}. "
                    f"Features include high-end fixtures, peaceful neighborhood, LDA/CDA/DHA approved layout, "
                    f"close proximity to {schools[0]} and {hospitals[0]}."
                )

                cursor.execute("""
                    INSERT INTO properties (
                        title, city, area, price_pkr, price_formatted, size_val, size_unit,
                        bedrooms, bathrooms, purpose, property_type, status, developer,
                        description, amenities, nearby_schools, nearby_hospitals
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title, city, area, price, price_fmt, tmpl["size_val"], tmpl["unit"],
                    tmpl["beds"], tmpl["baths"], purpose, tmpl["type"], "Available", dev,
                    desc, json.dumps(amenities_sample), ", ".join(schools), ", ".join(hospitals)
                ))
                
                prop_id = cursor.lastrowid
                
                # Add payment plan for Sale items
                if purpose == "Sale":
                    down_payment = round(price * 0.25, -4)
                    monthly_inst = round((price - down_payment) / 36, -3)
                    cursor.execute("""
                        INSERT INTO payment_plans (
                            property_id, down_payment_pkr, monthly_installment_pkr, duration_months, possession_months
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (prop_id, down_payment, monthly_inst, 36, 18))

    # Seed Agents
    agents_data = [
        ("Tariq Mahmood", "+92-300-8451199", "tariq.mahmood@realestatehub.pk", "Lahore", 4.9),
        ("Shehryar Khan", "+92-321-9988112", "shehryar.khan@realestatehub.pk", "Islamabad", 4.8),
        ("Zeeshan Siddiqui", "+92-333-2211445", "zeeshan.siddiqui@realestatehub.pk", "Karachi", 4.9),
        ("Ayesha Chaudhry", "+92-301-5544332", "ayesha.chaudhry@realestatehub.pk", "Lahore", 4.7),
        ("Hamza Malik", "+92-312-7766554", "hamza.malik@realestatehub.pk", "Islamabad", 4.8)
    ]
    for a in agents_data:
        cursor.execute("INSERT INTO agents (name, phone, email, city_specialty, rating) VALUES (?, ?, ?, ?, ?)", a)

    # Seed FAQs
    faqs_data = [
        ("Transfer & Legal", "DHA transfer procedure requirements kya hain?", "DHA transfer ke liye CNIC copies, Allotment Letter, NDC (No Demand Certificate), aur tax paid challans darkaar hotay hain. Direct owner transfer 3 se 5 working days mein ho jata hai."),
        ("Payment Policy", "Kya installment plans par discount milta hai?", "Ji bilkul! Agar aap full cash payment front pay karain to developer ki taraf se 10% se 15% tak upfront cash discount offer kiya jata hai."),
        ("Verification & NOC", "Kya Bahria Town aur Emaar properties RDA/LDA/CDA approved hain?", "Ji 100% approved hain! Emaar Crescent Bay Karachi aur Bahria Town Lah/Isb tamam relevant regulatory authorities (LDA, CDA, SBCA) se clear hain."),
        ("Overseas Pakistani", "Overseas Pakistanis ke liye special booking process kya hai?", "Overseas client Power of Attorney (PoA) ke zariye online booking kara sakte hain. Direct bank transfer through Roshan Digital Account (RDA) easily supported hai.")
    ]
    for f in faqs_data:
        cursor.execute("INSERT INTO faqs (category, question, answer) VALUES (?, ?, ?)", f)

    conn.commit()
    conn.close()
    print(f"Successfully seeded {properties_count} properties into SQLite database.")

if __name__ == "__main__":
    seed_database()
