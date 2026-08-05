from pathlib import Path
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


UPLOADS_DIR = BASE_DIR / os.getenv(
    "UPLOADS_DIR",
    "uploads",
)
REPORTS_DIR = BASE_DIR / os.getenv(
    "REPORTS_DIR",
    "reports",
)
DATA_DIR = BASE_DIR / os.getenv(
    "DATA_DIR",
    "data",
)

UPLOADS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(
        os.getenv("DB_PORT", "5432")
    ),
}


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)
JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "480")
)