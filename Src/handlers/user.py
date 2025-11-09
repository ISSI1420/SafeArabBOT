from aiogram import types, Dispatcher
from ..database import get_user_deals, get_user_rating
from .menu import main_menu

async def show_my_deals(call: types.CallbackQuery):
    uid = call.from_user.id
    deals = get_user_deals(uid)
    if not deals:
        await call.message.edit_text("ليس لديك أي صفقات بعد.", reply_markup=main_menu(uid))
        return
    txt = "سجل صفقاتك:\n\n"
    for d in deals[:12]:
        state = d[6]
        deal_id = d[0]
        txt += f"#{deal_id} | {d[3]} {d[4]} | {state}\n"
    await call.message.edit_text(txt, reply_markup=main_menu(uid))

async def my_rating_screen(call: types.CallbackQuery):
    count, total = get_user_rating(call.from_user.id)
    score = round(total / count, 2) if count > 0 else "-"
    await call.message.edit_text(f"تقييمك: ⭐️ {score} (عدد التقييمات: {count})", reply_markup=main_menu(call.from_user.id))

def register(dp: Dispatcher):
    dp.register_callback_query_handler(show_my_deals, lambda c: c.data == "my_deals")
    dp.register_callback_query_handler(my_rating_screen, lambda c: c.data == "my_rating")