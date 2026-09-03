import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import config

DB_PATH = config.DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create properties table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        city TEXT NOT NULL,
        area TEXT NOT NULL,
        price_pkr REAL NOT NULL,
        price_formatted TEXT NOT NULL,
        size_val REAL NOT NULL,
        size_unit TEXT NOT NULL,
        bedrooms INTEGER DEFAULT 0,
        bathrooms INTEGER DEFAULT 0,
        purpose TEXT NOT NULL,
        property_type TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        developer TEXT NOT NULL,
        description TEXT,
        amenities TEXT,
        nearby_schools TEXT,
        nearby_hospitals TEXT
    )
    """)
    
    # 2. Create payment_plans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER,
        down_payment_pkr REAL NOT NULL,
        monthly_installment_pkr REAL NOT NULL,
        duration_months INTEGER NOT NULL,
        possession_months INTEGER NOT NULL,
        FOREIGN KEY (property_id) REFERENCES properties (id)
    )
    """)
    
    # 3. Create agents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT DEFAULT 'manager@realestatehub.pk',
        city_specialty TEXT NOT NULL,
        rating REAL DEFAULT 4.8
    )
    """)
    
    cursor.execute("PRAGMA table_info(agents)")
    columns = [col[1] for col in cursor.fetchall()]
    if "email" not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN email TEXT DEFAULT 'manager@realestatehub.pk'")

    # 4. Create faqs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )
    """)
    
    # 5. Create appointments table (Day 4 Automation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        client_name TEXT NOT NULL,
        client_phone TEXT NOT NULL,
        client_email TEXT NOT NULL,
        employee_name TEXT NOT NULL,
        employee_email TEXT NOT NULL,
        property_title TEXT NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        status TEXT DEFAULT 'BOOKED',
        calendar_event_id TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- CRM LOGGING STORE TABLES ---
    # 6. CRM Call Transcripts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crm_call_transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        client_email TEXT NOT NULL,
        raw_transcript TEXT NOT NULL,
        normalized_transcript TEXT NOT NULL,
        agent_response TEXT NOT NULL,
        latency_sec REAL DEFAULT 0.0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. CRM Client Preferences
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crm_client_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_email TEXT UNIQUE NOT NULL,
        preferred_city TEXT,
        preferred_area TEXT,
        max_budget_pkr REAL,
        bedrooms INTEGER,
        property_type TEXT,
        purpose TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. CRM Appointment History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crm_appointment_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        client_email TEXT NOT NULL,
        action_type TEXT NOT NULL, -- 'BOOKING', 'RESCHEDULING', 'CANCELLATION'
        details TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 9. CRM Follow-up Reminders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crm_followup_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_email TEXT NOT NULL,
        client_name TEXT NOT NULL,
        reminder_type TEXT NOT NULL, -- 'Pre-Visit Call', 'Price Discount Check', 'Legal Documents'
        reminder_date TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING', -- 'PENDING', 'COMPLETED'
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def query_properties_sql(
    city: Optional[str] = None,
    area: Optional[str] = None,
    max_price_pkr: Optional[float] = None,
    min_price_pkr: Optional[float] = None,
    bedrooms: Optional[int] = None,
    purpose: Optional[str] = None,
    property_type: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM properties WHERE status = 'Available'"
    params = []
    
    if city:
        query += " AND LOWER(city) LIKE LOWER(?)"
        params.append(f"%{city}%")
    if area:
        query += " AND LOWER(area) LIKE LOWER(?)"
        params.append(f"%{area}%")
    if max_price_pkr:
        query += " AND price_pkr <= ?"
        params.append(max_price_pkr)
    if min_price_pkr:
        query += " AND price_pkr >= ?"
        params.append(min_price_pkr)
    if bedrooms:
        query += " AND bedrooms >= ?"
        params.append(bedrooms)
    if purpose:
        query += " AND LOWER(purpose) = LOWER(?)"
        params.append(purpose)
    if property_type:
        query += " AND LOWER(property_type) = LOWER(?)"
        params.append(property_type)
        
    query += " ORDER BY price_pkr ASC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    result = []
    for r in rows:
        item = dict(r)
        if item.get("amenities"):
            try:
                item["amenities"] = json.loads(item["amenities"])
            except Exception:
                item["amenities"] = [a.strip() for a in item["amenities"].split(",") if a.strip()]
        result.append(item)
        
    conn.close()
    return result

def get_agent_by_city(city: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE LOWER(city_specialty) LIKE LOWER(?) LIMIT 1", (f"%{city}%",))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        agent_dict = dict(row)
        if not agent_dict.get("email"):
            agent_dict["email"] = f"{agent_dict['name'].lower().replace(' ', '.')}@realestatehub.pk"
        return agent_dict
    
    # Fallbacks by city
    if "lahore" in (city or "").lower():
        return {"name": "Tariq Mahmood", "phone": "+92-300-8451199", "email": "tariq.mahmood@realestatehub.pk", "city_specialty": "Lahore", "rating": 4.9}
    elif "islamabad" in (city or "").lower():
        return {"name": "Shehryar Khan", "phone": "+92-321-9988112", "email": "shehryar.khan@realestatehub.pk", "city_specialty": "Islamabad", "rating": 4.8}
    elif "karachi" in (city or "").lower():
        return {"name": "Zeeshan Siddiqui", "phone": "+92-333-2211445", "email": "zeeshan.siddiqui@realestatehub.pk", "city_specialty": "Karachi", "rating": 4.9}
    else:
        return {"name": "Tariq Mahmood", "phone": "+92-300-8451199", "email": "tariq.mahmood@realestatehub.pk", "city_specialty": "Lahore", "rating": 4.9}

if __name__ == "__main__":
    init_db()
    print("Database initialized with CRM Logging Store tables successfully.")
