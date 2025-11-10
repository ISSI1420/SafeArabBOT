import os
from dotenv import load_dotenv
from typing import List

# تحميل المتغيرات من ملف .env
load_dotenv()

def _parse_admin_ids(value: str) -> list[int]:
    """
    تحويل قيمة ADMIN_IDS من سلسلة مفصولة بفواصل إلى قائمة أرقام.
    """
    if not value:
        return []
    out: list[int] = []
    for p in value.split(","):
        p = p.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out

# -----------------------------
# إعدادات البوت
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
TON_WALLET = os.getenv("TON_WALLET", "").strip()
TON_API_KEY = os.getenv("TON_API_KEY", "").strip()
TON_SEED = os.getenv("TON_SEED", "").strip()

# -----------------------------
# إعدادات قاعدة البيانات
# -----------------------------
# رابط قاعدة البيانات الخارجية (Postgres / Supabase)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# تحذير لو لم يتم تعيين BOT_TOKEN
if not BOT_TOKEN:
    print("Warning: BOT_TOKEN not set. Bot may not run correctly.")
