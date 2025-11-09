from aiogram import types, Dispatcher
from ..database import get_blacklist
from .menu import main_menu

async def blacklist_screen(call: types.CallbackQuery):
    bl = get_blacklist()
    txt = "قائمة النصابين:\n"
    for x in bl:
        txt += f"• {x[0]} | سبب: {x[1]}\n"
    if not bl:
        txt = "لا يوجد نصابين حالياً."
    await call.message.edit_text(txt, reply_markup=main_menu(call.from_user.id))

def register(dp: Dispatcher):
    dp.register_callback_query_handler(blacklist_screen, lambda c: c.data == "blacklist")