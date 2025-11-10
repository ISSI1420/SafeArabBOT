import os
from dotenv import load_dotenv
from typing import List

# Load .env from project root
load_dotenv()

def _parse_admin_ids(value: str) -> list[int]:
    if not value:
        return []
    parts = [p.strip() for p in value.split(",") if p.strip()]
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out

# BOT settings
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
TON_WALLET = os.getenv("TON_WALLET", "").strip()
TON_API_KEY = os.getenv("TON_API_KEY", "").strip()
TON_SEED = os.getenv("TON_SEED", "").strip()

# -----------------------------
# Database settings
# -----------------------------
# مسار ثابت لقاعدة البيانات داخل مجلد Data الذي ستنشئه بنفسك
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "safearab.db")

# تحذير لو لم يتم تعيين BOT_TOKEN
if not BOT_TOKEN:
    print("Warning: BOT_TOKEN not set. Bot may not run correctly.")
