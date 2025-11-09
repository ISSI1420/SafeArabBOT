from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from ..states import DealState
from ..database import (
    add_deal, get_user, get_user_wallet, get_deal, update_deal_state,
    complete_deal, set_deal_tx_hash, add_rating, is_blacklisted
)
from ..utils import is_valid_ton_address, generate_deal_memo
from ..config import ADMIN_IDS, TON_WALLET, BOT_COMMISSION_PERCENT
from .menu import main_menu
from ..wallet import send_ton

async def start_deal(call: types.CallbackQuery):
    await call.message.edit_text(
        "اختر نوع الصفقة:",
        reply_markup=types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("شراء", callback_data="deal_mode_buy"),
            types.InlineKeyboardButton("بيع", callback_data="deal_mode_sell"),
            types.InlineKeyboardButton("خدمة", callback_data="deal_mode_service"),
            types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")
        )
    )
    await DealState.select_mode.set()

async def deal_mode_select(call: types.CallbackQuery, state: FSMContext):
    mode = call.data.replace("deal_mode_", "")
    await state.update_data(mode=mode)
    await call.message.edit_text("أدخل اسم مستخدم الطرف الآخر (بدون @):")
    await DealState.select_partner.set()

async def deal_enter_partner(message: types.Message, state: FSMContext):
    partner_username = message.text.replace("@", "").strip()
    partner = get_user_by_username(partner_username)
    if not partner:
        await message.reply("المستخدم غير موجود أو لم يسجل في البوت بعد.")
        return
    if is_blacklisted(partner[1]):
        await message.reply("تحذير: هذا الطرف في القائمة السوداء!")
    await state.update_data(partner_username=partner_username, partner_id=partner[1])
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("TON 💠", callback_data="deal_curr_TON"),
        types.InlineKeyboardButton("USDT-TON 💵", callback_data="deal_curr_USDT"),
        types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")
    )
    await message.answer("اختر العملة المطلوبة:", reply_markup=kb)
    await DealState.select_currency.set()

async def deal_currency_select(call: types.CallbackQuery, state: FSMContext):
    currency = call.data.replace("deal_curr_", "")
    await state.update_data(currency=currency)
    await call.message.edit_text("أدخل مبلغ الصفقة بالعملة المختارة:")
    await DealState.enter_amount.set()

async def deal_enter_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise Exception
    except Exception:
        return await message.reply("❌ مبلغ غير صحيح. أعد المحاولة.")
    await state.update_data(amount=amount)
    await message.answer("اكتب وصفًا مختصرًا للسلعة أو الخدمة:")
    await DealState.enter_description.set()

async def deal_enter_desc(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(description=desc)
    data = await state.get_data()
    partner_username = data['partner_username']
    currency = data['currency']
    amount = data['amount']
    confirm_txt = (
        f"ملخص الصفقة:\nالطرف الآخر: @{partner_username}\n"
        f"العملة: {currency}\nالمبلغ: {amount}\nالوصف: {desc}\n\n"
        "هل ترغب في إرسال الصفقة للطرف الآخر؟"
    )
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✔️ إرسال", callback_data="deal_yes"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="deal_cancel"),
    )
    await message.answer(confirm_txt, reply_markup=kb)
    await DealState.confirm.set()

async def deal_confirm_or_cancel(call: types.CallbackQuery, state: FSMContext):
    if call.data == "deal_yes":
        data = await state.get_data()
        user_id = call.from_user.id
        partner_id = data['partner_id']
        mode = data['mode']
        currency = data['currency']
        amount = data['amount']
        description = data['description']
        buyer_id, seller_id = (user_id, partner_id) if mode == "buy" else (partner_id, user_id)
        memo = generate_deal_memo(buyer_id + seller_id)
        deal_id = add_deal(buyer_id, seller_id, currency, amount, description, memo)
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("✔️ موافقة", callback_data=f"deal_accept_{deal_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"deal_reject_{deal_id}")
        )
        try:
            await call.bot.send_message(partner_id, f"لديك صفقة جديدة من @{call.from_user.username}.\nالمبلغ: {amount} {currency}\nالوصف: {description}", reply_markup=kb)
        except:
            await call.message.edit_text("❌ الطرف الآخر لم يبدأ البوت بعد.", reply_markup=main_menu(user_id))
            await state.finish()
            return
        await call.message.edit_text("تم إرسال الصفقة للطرف الآخر وتنتظر الموافقة.", reply_markup=main_menu(user_id))
        await state.finish()
    else:
        await call.message.edit_text("تم إلغاء العملية.", reply_markup=main_menu(call.from_user.id))
        await state.finish()

async def deal_accept_reject(call: types.CallbackQuery, state: FSMContext):
    is_accept = "accept" in call.data
    deal_id = int(call.data.split("_")[-1])
    deal = get_deal(deal_id)
    if not deal:
        return await call.answer("❌ الصفقة غير موجودة.")
    if not is_accept:
        update_deal_state(deal_id, "cancelled")
        await call.message.edit_text("تم رفض الصفقة.", reply_markup=main_menu(call.from_user.id))
        try:
            await call.bot.send_message(deal[1], "تم رفض الصفقة من الطرف الآخر.")
        except:
            pass
        return
    update_deal_state(deal_id, "waiting_deposit")
    amount = deal[4]
    currency = deal[3]
    memo = deal[10]
    instr = (
        f"لإتمام الصفقة أرسل: {amount} {currency}\n"
        f"على عنوان المحفظة التالية:\n\n"
        f"`{TON_WALLET}`\n\n"
        f"وضع ميمو (Transaction memo): `{memo}`\n\n"
        "بعد الإرسال، اضغط الزر التالي لتأكيد الدفع."
    )
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("💸 تم الدفع", callback_data=f"user_paid_{deal_id}")
    )
    try:
        await call.bot.send_message(deal[1], instr, parse_mode="Markdown", reply_markup=kb)
    except:
        pass
    await call.message.edit_text("تمت الموافقة على الصفقة. في انتظار إيداع المشتري…", reply_markup=main_menu(call.from_user.id))

async def user_paid(call: types.CallbackQuery, state: FSMContext):
    deal_id = int(call.data.split("_")[-1])
    deal = get_deal(deal_id)
    if not deal:
        return await call.answer("❌ الصفقة غير موجودة.")
    update_deal_state(deal_id, "deposited")
    await call.message.edit_text(
        "تم رصد التحويل! بدأ تنفيذ الصفقة.\n\nعلى البائع تسليم المنتج أو الخدمة ثم ينتظر تأكيد المشتري.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("فتح نزاع 🚨", callback_data=f"dispute_{deal_id}"),
            types.InlineKeyboardButton("✅ تم الاستلام", callback_data=f"buyer_received_{deal_id}"),
            types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"),
        )
    )
    try:
        await call.bot.send_message(deal[2], f"تم تأكيد إيداع الضمان من المشتري. يمكنك الآن تسليم ورفع الخدمة.")
    except:
        pass

async def buyer_received(call: types.CallbackQuery, state: FSMContext):
    deal_id = int(call.data.split("_")[-1])
    deal = get_deal(deal_id)
    if not deal or deal[6] == "completed":
        await call.answer("❌ الصفقة غير موجودة أو مكتملة.")
        return
    amount = deal[4]
    seller_wallet = get_user_wallet(deal[2])
    commission = amount * BOT_COMMISSION_PERCENT
    payout = amount - commission
    # الدفع التلقائي للبائع
    try:
        txid = await send_ton(seller_wallet, payout, comment=f"Release Escrow deal {deal_id}")
        set_deal_tx_hash(deal_id, str(txid))
    except Exception as e:
        await call.message.answer(f"حدث خطأ في التحويل الآلي: {str(e)}")
        return
    complete_deal(deal_id)
    await call.message.edit_text("✅ تم إنهاء الصفقة وتحويل المبلغ للبائع (بعد خصم العمولة)!\nيرجى تقييم الطرف الآخر بواسطة /rate", reply_markup=main_menu(call.from_user.id))
    try:
        await call.bot.send_message(deal[2], "✅ تم إنهاء الصفقة وتحويل رصيدك.")
    except:
        pass

async def open_dispute(call: types.CallbackQuery, state: FSMContext):
    deal_id = int(call.data.split("_")[-1])
    await state.update_data(deal_id=deal_id)
    await call.message.answer("يرجى شرح سبب النزاع أو الخلاف (سيُرسل للإدارة):")
    await DealState.dispute_msg.set()

async def dispute_msg_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    deal_id = data.get("deal_id")
    if not deal_id:
        return
    update_deal_state(deal_id, "dispute")
    txt = f"🚨 نزاع في صفقة رقم [{deal_id}]!\nسبب النزاع: {message.text}"
    for a in ADMIN_IDS:
        try:
            await message.bot.send_message(a, txt)
        except:
            pass
    await message.answer("تم فتح النزاع، وسيتواصل معك الأدمن لاتخاذ القرار.", reply_markup=main_menu(message.from_user.id))
    await state.finish()

def get_user_by_username(username):
    from ..database import db
    conn, cur = db()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

def register(dp: Dispatcher):
    dp.register_callback_query_handler(start_deal, lambda c: c.data == "new_deal")
    dp.register_callback_query_handler(deal_mode_select, lambda c: c.data.startswith("deal_mode_"), state=DealState.select_mode)
    dp.register_message_handler(deal_enter_partner, state=DealState.select_partner)
    dp.register_callback_query_handler(deal_currency_select, lambda c: c.data.startswith("deal_curr_"), state=DealState.select_currency)
    dp.register_message_handler(deal_enter_amount, state=DealState.enter_amount)
    dp.register_message_handler(deal_enter_desc, state=DealState.enter_description)
    dp.register_callback_query_handler(deal_confirm_or_cancel, state=DealState.confirm)
    dp.register_callback_query_handler(deal_accept_reject, lambda c: c.data.startswith("deal_accept_") or c.data.startswith("deal_reject_"), state="*")
    dp.register_callback_query_handler(user_paid, lambda c: c.data.startswith("user_paid_"), state="*")
    dp.register_callback_query_handler(buyer_received, lambda c: c.data.startswith("buyer_received_"), state="*")
    dp.register_callback_query_handler(open_dispute, lambda c: c.data.startswith("dispute_"), state="*")
    dp.register_message_handler(dispute_msg_entered, state=DealState.dispute_msg)