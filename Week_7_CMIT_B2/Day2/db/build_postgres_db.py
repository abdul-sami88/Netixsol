"""
build_postgres_db.py — loads the knowledge base CSVs into a real Postgres
database using `schema_postgres.sql`.

NOTE: This sandbox has no network access to an external Postgres instance,
so this script is written to be correct and production-ready but has not
been executed here (unlike build_db.py/SQLite, which has been run and
verified end-to-end in this environment). Test it against your own
Postgres instance before relying on it.

Usage:
    pip install psycopg2-binary
    export PG_DSN="postgresql://user:password@host:5432/dbname"
    python3 build_postgres_db.py
"""
import os
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SCHEMA_FILE = os.path.join(HERE, "schema_postgres.sql")

TABLE_FILES = {
    "properties": "properties.csv",
    "locations": "locations.csv",
    "amenities": "amenities.csv",
    "schools": "schools.csv",
    "hospitals": "hospitals.csv",
    "payment_plans": "payment_plans.csv",
    "developers": "developers.csv",
    "faqs": "faqs.csv",
    "property_description_chunks": "descriptions.csv",  # id, property_id, text
}

# Postgres BOOLEAN needs 'true'/'false' rather than Python's True/False str,
# and CSV empty strings need to become NULL for numeric/FK columns.
BOOL_COLUMNS = {"hospitals": {"emergency_services"}}


def load_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def coerce_row(table, row):
    out = {}
    for k, v in row.items():
        if v == "":
            out[k] = None
        elif table in BOOL_COLUMNS and k in BOOL_COLUMNS[table]:
            out[k] = str(v).strip().lower() in ("true", "1", "yes")
        else:
            out[k] = v
    return out


def main():
    import psycopg2
    from psycopg2.extras import execute_values

    dsn = os.environ.get("PG_DSN")
    if not dsn:
        raise SystemExit("Set PG_DSN, e.g. postgresql://user:pass@host:5432/dbname")

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    with open(SCHEMA_FILE) as f:
        cur.execute(f.read())
    conn.commit()
    print("Schema + indexes created.")

    for table, fname in TABLE_FILES.items():
        rows = [coerce_row(table, r) for r in load_csv_rows(os.path.join(DATA, fname))]
        if not rows:
            continue
        cols = list(rows[0].keys())
        values = [tuple(r[c] for c in cols) for r in rows]
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES %s"
        execute_values(cur, sql, values)
        conn.commit()
        print(f"loaded {len(rows)} rows into {table}")

    cur.close()
    conn.close()
    print("Postgres DB build complete.")


if __name__ == "__main__":
    main()
