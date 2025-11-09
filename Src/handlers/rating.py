from aiogram import types, Dispatcher
from ..database import add_rating
from .menu import main_menu

async def submit_rating(message: types.Message):
    data = message.text.strip().split()
    if len(data) < 3:
        await message.answer("أرسل: رقم_الصفقة رقم_الطرف تقييم(1-5) [ملاحظة]")
        return
    deal_id, to_user, rate = map(int, data[:3])
    comment = " ".join(data[3:]) if len(data) > 3 else ""
    add_rating(deal_id, message.from_user.id, to_user, rate, comment)
    await message.answer("تم حفظ تقييمك. شكراً!", reply_markup=main_menu(message.from_user.id))

def register(dp: Dispatcher):
    dp.register_message_handler(submit_rating, commands=['rate'])