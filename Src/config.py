import os
from dotenv import load_dotenv
from typing import List

# Load .env from project root
load_dotenv()

def _parse_admin_ids(value: str) -> List[int]:
    if not value:
        return []
    parts = [p.strip() for p in value.split(",") if p.strip()]
    out: List[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            # ignore invalid entries
            continue
    return out

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
TON_WALLET = os.getenv("TON_WALLET", "").strip()
TON_API_KEY = os.getenv("TON_API_KEY", "").strip()
TON_SEED = os.getenv("TON_SEED", "").strip()
# إنشاء مجلد Data داخل نفس مجلد config.py لو مش موجود
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
os.makedirs(DATA_DIR, exist_ok=True)

# قاعدة البيانات داخل المجلد Data
DB_FILE = os.path.join(DATA_DIR, "safearab.db")

# Small sanity checks for helpful logs
if not BOT_TOKEN:
    # It's okay to run tests without token, but warn in logs at runtime
    pass
