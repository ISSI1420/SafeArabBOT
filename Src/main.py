import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from . import config, database
from .handlers import menu, deal, user, admin, rating, blacklist, referral

def main():
    logging.basicConfig(level=logging.INFO)
    database.init_db()
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())
    menu.register(dp)
    deal.register(dp)
    user.register(dp)
    rating.register(dp)
    admin.register(dp)
    blacklist.register(dp)
    referral.register(dp)
    executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    main()