import logging
import sys
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from . import config, database

def _safe_register_handlers(dp: Dispatcher):
    # Register handlers dynamically from Src.handlers package if present
    handler_modules = ["menu", "deal", "user", "rating", "admin", "blacklist", "referral"]
    for mod_name in handler_modules:
        try:
            mod = __import__(f"Src.handlers.{mod_name}", fromlist=["register"]) if True else None
            if mod and hasattr(mod, "register"):
                mod.register(dp)
                logging.info(f"Registered handler module: {mod_name}")
        except Exception as e:
            logging.warning(f"Could not register handler '{mod_name}': {e}")

def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s")
    logging.info("Starting SafeArabBOT...")

    # Sanity check for token
    if not config.BOT_TOKEN:
        logging.critical("BOT_TOKEN is not set. Please set BOT_TOKEN in environment or .env file.")
        sys.exit(1)

    # Initialize DB
    try:
        database.init_db()
    except Exception as e:
        logging.exception(f"Failed to initialize database: {e}")
        sys.exit(1)

    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Try to register known handlers (silently continue if not present)
    _safe_register_handlers(dp)

    logging.info("Starting polling...")
    executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    main()
