"""
Database Connection and Session Management
Supports both PostgreSQL (Supabase / Render / Local) and local SQLite fallback.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.database.models import Base

# Load environment variables
load_dotenv()

# Project Root & Data Directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database URL resolution
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    sqlite_path = DATA_DIR / "city_care_clinics.db"
    final_url = f"sqlite:///{sqlite_path}"
    engine_kwargs = {"echo": False, "connect_args": {"check_same_thread": False}}
else:
    # PostgreSQL Engine Configuration
    engine_kwargs = {
        "echo": False,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }
    # Parse PostgreSQL credentials safely (handles special characters like '@' in password)
    try:
        prefix, rest = DATABASE_URL.split("://", 1)
        auth_part, host_part = rest.rsplit("@", 1)
        user, password = auth_part.split(":", 1)
        
        if "/" in host_part:
            host_port, dbname = host_part.split("/", 1)
        else:
            host_port, dbname = host_part, "city_care_clinics"

        host = host_port.split(":")[0] if ":" in host_port else host_port
        port = int(host_port.split(":")[1]) if ":" in host_port else 5432

        from sqlalchemy.engine import URL
        final_url = URL.create(
            drivername="postgresql+psycopg2",
            username=user,
            password=password,
            host=host,
            port=port,
            database=dbname
        )
    except Exception:
        final_url = DATABASE_URL

engine = create_engine(final_url, **engine_kwargs)

# Create thread-safe session factory
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionFactory)


def init_db():
    """Initializes and creates all database tables."""
    Base.metadata.create_all(bind=engine)
    return engine


def get_db():
    """Yields a database session context."""
    db = db_session()
    try:
        yield db
    finally:
        db.close()
