from aiogram import types, Dispatcher

def main_menu(user_id):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🆕 بدء صفقة جديدة", callback_data="new_deal"))
    kb.add(InlineKeyboardButton("💼 صفقاتي", callback_data="my_deals"))
    kb.add(InlineKeyboardButton("✉️ نظام الإحالة", callback_data="referral"))
    kb.add(InlineKeyboardButton("⭐ تقييمي", callback_data="my_rating"))
    kb.add(InlineKeyboardButton("👥 قائمة النصابين", callback_data="blacklist"))
    kb.add(InlineKeyboardButton("ℹ️ معلومات", callback_data="about"))
    kb.add(InlineKeyboardButton("🛡️ لوحة الإدارة", callback_data="admin_panel"))
    return kb

async def start_handler(message: types.Message):
    user_id = message.from_user.id
    await message.answer("مرحباً بك في بوت الوساطة عبر TON/USDT-TON!\nكل شيء يتم بالأمان، والتقييم، وعمولة 2%.", reply_markup=main_menu(user_id))

async def menu_callback(call: types.CallbackQuery):
    d = call.data
    u = call.from_user
    if d == "main_menu":
        await call.message.edit_text("مرحباً بك في القائمة الرئيسية.", reply_markup=main_menu(u.id))

def register(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=['start'])
    dp.register_callback_query_handler(menu_callback)