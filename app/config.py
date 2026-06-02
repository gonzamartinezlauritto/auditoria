from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

UPLOADS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

DB_CONFIG = {
    "host": "localhost",
    "dbname": "quiniela_db",
    "user": "postgres",
    "password": "loteria",
    "port": 5432,
}