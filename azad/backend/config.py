"""
Azad Foundation MIS - Configuration
"""
import os
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Database connection settings
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "mis_lms_db")
DB_SCHEMA = os.environ.get("DB_SCHEMA", "mis_azad")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?options=-csearch_path%3D{DB_SCHEMA}%2Cpublic"
)

# For JWT authentication
JWT_SECRET = os.environ.get("JWT_SECRET", "azad-mis-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# File uploads
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Email / SMTP settings
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "azad@azadfoundationindia.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "rkii jpfr frhd khmo")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "azad@azadfoundationindia.com")
# 2026-05-28: FLP survey-submission notifications now go to the FLP
# programme team's shared inbox instead of an individual admin's
# address. The .env on each environment overrides this default; the
# fallback was updated so that a fresh deploy without .env still ends
# up at the right inbox.
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "infoflp@azadfoundationindia.com")
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "true").lower() == "true"
