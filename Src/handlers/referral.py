from aiogram import types, Dispatcher
from ..database import get_user, get_user_referrals
from .menu import main_menu

async def referral_screen(call: types.CallbackQuery):
    uid = call.from_user.id
    me = await call.bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    user = get_user(uid)
    total_earn = user[7] if user else 0
    refs = get_user_referrals(uid)
    txt = f"رابط الإحالة الخاص بك:\n{link}\n\nعدد الإحالات المنجزة: {len(refs)}\nأرباحك: {total_earn:.2f} TON/USDT-TON"
    await call.message.edit_text(txt, reply_markup=main_menu(uid))

def register(dp: Dispatcher):
    dp.register_callback_query_handler(referral_screen, lambda c: c.data == "referral")