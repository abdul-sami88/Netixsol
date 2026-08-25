import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


DB_PASS = os.getenv("DB_PASS")
# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="properties",
        user="postgres",
        password=DB_PASS,
        port=5432
    )


# ============================================================
# PROPERTY RECOMMENDATION
# ============================================================

def recommend_properties(
    location=None,
    property_type=None,
    max_price=None,
    min_price=None,
    plot_size=None,
    bedrooms=None,
    limit=5
):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            property_id,
            location,
            property_type,
            price,
            plot_size,
            bedrooms,
            page_url
        FROM properties
        WHERE 1=1
    """

    params = []

    # Location
    if location:
        query += " AND LOWER(location) = LOWER(%s)"
        params.append(location)

    # Property type
    if property_type:
        query += " AND LOWER(property_type) = LOWER(%s)"
        params.append(property_type)

    # Maximum price
    if max_price:
        query += " AND price <= %s"
        params.append(max_price)

    # Minimum price
    if min_price:
        query += " AND price >= %s"
        params.append(min_price)

    # Plot size
    if plot_size:
        query += " AND plot_size = %s"
        params.append(plot_size)

    # Bedrooms
    if bedrooms:
        query += " AND bedrooms >= %s"
        params.append(bedrooms)

    query += " ORDER BY price ASC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)

    properties = cursor.fetchall()

    cursor.close()
    conn.close()

    return properties


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    results = recommend_properties(
        location="Faisalabad",
        property_type="House",
        max_price=20000000,
        plot_size=5,
        bedrooms=3
    )

    if not results:
        print("Sorry, I couldn't find any matching properties.")

    else:
        print(f"Found {len(results)} properties:\n")

        for property in results:
            print(
                f"Property ID: {property[0]}\n"
                f"Location: {property[1]}\n"
                f"Type: {property[2]}\n"
                f"Price: {property[3]}\n"
                f"Plot Size: {property[4]} Marla\n"
                f"Bedrooms: {property[5]}\n"
                f"URL: {property[6]}\n"
            )
