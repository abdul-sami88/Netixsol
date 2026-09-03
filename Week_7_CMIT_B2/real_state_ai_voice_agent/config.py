import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def clean_env(val: str) -> str:
    if not val:
        return ""
    return val.strip().strip('"').strip("'")

class Config:
    # LLM Settings
    GEMINI_API_KEY: str = clean_env(os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = clean_env(os.getenv("GEMINI_MODEL", "gemini-3.5-flash"))
    
    GROQ_API_KEY: str = clean_env(os.getenv("GROQ_API_KEY", ""))
    GROQ_MODEL: str = clean_env(os.getenv("GROQ_MODEL"))
    
    # Voice Provider Keys
    DEEPGRAM_API_KEY: str = clean_env(os.getenv("DEEPGRAM_API_KEY"))
    ELEVENLABS_API_KEY: str = clean_env(os.getenv("ELEVENLABS_API_KEY"))
    ELEVENLABS_VOICE_ID: str = clean_env(os.getenv("ELEVENLABS_VOICE_ID"))
    
    VAPI_API_KEY: str = clean_env(os.getenv("VAPI_API_KEY"))
    VAPI_ASSISTANT_ID: str = clean_env(os.getenv("VAPI_ASSISTANT_ID"))
    SUPER_SECRET: str = clean_env(os.getenv("SUPER_SECRET"))

     # Server Host & Port
    HOST: str = clean_env(os.getenv("HOST", "127.0.0.1"))
    PORT: int = int(clean_env(os.getenv("PORT", "8000")) or "8000")
    
    # Google Calendar Settings
    GOOGLE_CALENDAR_ID: str = clean_env(os.getenv("GOOGLE_CALENDAR_ID", "primary"))
    GOOGLE_SERVICE_ACCOUNT_FILE: str = clean_env(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json"))
    
    # Email Automation Settings (SMTP)
    SMTP_SERVER: str = clean_env(os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = clean_env(os.getenv("SMTP_USERNAME", ""))
    SMTP_PASSWORD: str = clean_env(os.getenv("SMTP_PASSWORD", ""))
    NOTIFICATION_SENDER_EMAIL: str = clean_env(os.getenv("NOTIFICATION_SENDER_EMAIL", "notifications@realestatehub.pk"))
    
    # Database
    DATABASE_URL: str = clean_env(os.getenv("DATABASE_URL", "sqlite:///real_estate.db"))
    DB_PATH: Path = Path(__file__).parent / "real_estate.db"
    
    # Latency Target (seconds)
    TARGET_LATENCY_SEC: float = 2.0

config = Config()
