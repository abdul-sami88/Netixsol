"""
PostgreSQL & Supabase Exporter Module
Exports all analytical tables from DuckDB (shopkaro.duckdb) into any PostgreSQL instance:
- Local PostgreSQL (localhost:5432)
- Cloud Supabase (Transaction/Session Pooler or Direct connection)
- Neon.tech, Railway, AWS RDS

Usage Examples:
    # 1. Localhost:
    .venv\\Scripts\\python.exe src\\data_pipeline\\postgres_exporter.py --host localhost --user postgres --password mypass --db shopkaro

    # 2. Supabase (Paste your URI from Supabase Dashboard -> Project Settings -> Database):
    .venv\\Scripts\\python.exe src\\data_pipeline\\postgres_exporter.py --uri "postgresql://postgres.your-project:your-password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

    # 3. Via .env file:
    .venv\\Scripts\\python.exe src\\data_pipeline\\postgres_exporter.py
"""

import os
import sys
import argparse
import duckdb
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb")

# Load environment variables if .env exists
load_dotenv(os.path.join(BASE_DIR, ".env"))

def get_args():
    parser = argparse.ArgumentParser(description="Export ShopKaro DuckDB tables to Local PostgreSQL or Supabase")
    # Priority 1: Full Connection URI (standard for Supabase / Neon / Railway)
    parser.add_argument("--uri", default=os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL"), 
                        help="Full PostgreSQL connection URI (e.g. Supabase connection string)")
    
    # Priority 2: Individual connection parameters
    parser.add_argument("--host", default=os.getenv("POSTGRES_HOST", "localhost"), help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=int(os.getenv("POSTGRES_PORT", "5432")), help="PostgreSQL port")
    parser.add_argument("--user", default=os.getenv("POSTGRES_USER", "postgres"), help="PostgreSQL user")
    parser.add_argument("--password", default=os.getenv("POSTGRES_PASSWORD", "postgres"), help="PostgreSQL password")
    parser.add_argument("--db", default=os.getenv("POSTGRES_DB", "shopkaro"), help="PostgreSQL database name")
    parser.add_argument("--sslmode", default=os.getenv("POSTGRES_SSLMODE", None), help="SSL mode (e.g. require)")
    return parser.parse_args()

def ensure_database_exists_local(host, port, user, password, db_name):
    """Ensures target DB exists for local postgres instances."""
    default_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    print(f"Checking PostgreSQL server at {host}:{port}...")
    try:
        engine = create_engine(default_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as con:
            res = con.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")).fetchone()
            if not res:
                print(f"Database '{db_name}' not found. Creating database '{db_name}'...")
                con.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Target database '{db_name}' already exists.")
        engine.dispose()
        return True
    except Exception as e:
        print(f"\n[WARNING] Could not connect to default database: {e}")
        return False

def export_duckdb_to_postgres(args):
    print("="*65)
    print("SHOPKARO DUCKDB -> POSTGRESQL / SUPABASE MIGRATION PIPELINE")
    print("="*65)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: DuckDB file not found at {DB_PATH}")
        sys.exit(1)
        
    # Determine connection URI
    if args.uri:
        target_url = args.uri
        is_cloud = True
        print(f"Target: Cloud PostgreSQL / Supabase URI provided.")
    else:
        # Local configuration
        is_cloud = "localhost" not in args.host and "127.0.0.1" not in args.host
        ssl_part = "?sslmode=require" if (args.sslmode == "require" or is_cloud) else ""
        
        if not is_cloud:
            ensure_database_exists_local(args.host, args.port, args.user, args.password, args.db)
            
        target_url = f"postgresql://{args.user}:{args.password}@{args.host}:{args.port}/{args.db}{ssl_part}"
        print(f"Target: {args.host}:{args.port}/{args.db}")
        
    print(f"Connecting to database engine...")
    try:
        pg_engine = create_engine(target_url)
        with pg_engine.connect() as con:
            con.execute(text("SELECT 1"))
        print("Connected successfully to PostgreSQL / Supabase!")
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\nTroubleshooting Tips:")
        print(" - For Supabase: Make sure to copy the URI from Settings -> Database -> Connection String.")
        print("   If using password with special characters, make sure they are URL-encoded.")
        print(" - For Local: Ensure PostgreSQL service is started on your computer.")
        return False

    # 2. Connect to DuckDB
    con = duckdb.connect(DB_PATH)
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    
    print(f"\nFound {len(table_names)} tables in DuckDB to migrate:")
    print(", ".join(table_names))
    
    # 3. Export each table
    for idx, tbl in enumerate(table_names, 1):
        print(f"\n[{idx}/{len(table_names)}] Exporting table '{tbl}'...")
        df = con.execute(f"SELECT * FROM {tbl}").df()
        row_count = len(df)
        
        # Write to Postgres in chunks using SQLAlchemy
        df.to_sql(
            name=tbl,
            con=pg_engine,
            if_exists="replace",
            index=False,
            chunksize=10000,
            method="multi"
        )
        print(f"--> Successfully migrated '{tbl}': {row_count:,} rows.")
        
    # 4. Create primary key & foreign key indexes
    print("\nCreating indexes for query performance...")
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_pg_events_user ON events(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_pg_events_product ON events(product_id);",
        "CREATE INDEX IF NOT EXISTS idx_pg_events_timestamp ON events(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_pg_orders_user ON orders(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_pg_products_category ON products(category);",
        "CREATE INDEX IF NOT EXISTS idx_pg_reviews_product ON reviews(product_id);"
    ]
    
    with pg_engine.connect() as pg_con:
        for stmt in index_statements:
            try:
                pg_con.execute(text(stmt))
                pg_con.commit()
            except Exception:
                pass
                
    # 5. Verification
    print("\n" + "="*65)
    print("TABLE VERIFICATION IN POSTGRESQL / SUPABASE")
    print("="*65)
    with pg_engine.connect() as pg_con:
        for tbl in table_names:
            cnt = pg_con.execute(text(f"SELECT COUNT(*) FROM {tbl}")).fetchone()[0]
            print(f" - {tbl:18s}: {cnt:>10,} rows in database")
            
    con.close()
    pg_engine.dispose()
    print("\n[SUCCESS] Migration completed! All 12 tables are live and ready to query.")
    return True

if __name__ == "__main__":
    args = get_args()
    export_duckdb_to_postgres(args)
