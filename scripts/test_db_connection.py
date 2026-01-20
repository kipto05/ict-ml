import sys
import os

# Add parent folder (ict-ml) to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from config.settings import settings  # we assume settings.py reads .env

# Using DATABASE_URL from .env
engine = create_engine(settings.database_url)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection OK, test query returned:", result.fetchone())
except Exception as e:
    print("Database connection FAILED:", e)
