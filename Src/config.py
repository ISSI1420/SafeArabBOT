import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
TON_WALLET = os.getenv('TON_WALLET')
TON_API_KEY = os.getenv('TON_API_KEY')
TON_SEED = os.getenv('TON_SEED')
BOT_COMMISSION_PERCENT = 0.02
REFERRAL_COMMISSION_PERCENT = 0.02
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')