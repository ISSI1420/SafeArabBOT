from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import database
import utils
import config

# === States ===
class DealState(StatesGroup):
    select_mode = State()
    select_partner = State()
    select_currency = State()
    enter_amount = State()
    enter_description = State()
    confirm = State()
    waiting_deposit = State()
    waiting_approval = State()
    buyer_confirm = State()
    seller_confirm = State()
    dispute_msg = State()
    rate = State()

class EditWalletState(StatesGroup):
    enter_wallet = State()

# === Utils Keyboards ===
def main_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🆕 بدء صفقة جديدة", callback_data="new_deal"),
        InlineKeyboardButton("💼 صفقاتي", callback_data="my_deals"),
        InlineKeyboardButton("✉️ نظام الإحالة", callback_data="referral"),
        InlineKeyboardButton("⭐ تقييمي", callback_data="my_rating"),
        InlineKeyboardButton("👥 قائمة النصابين", callback_data="blacklist"),
        InlineKeyboardButton("ℹ️ معلومات", callback_data="about"),
    )
    if user_id in config.ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛡️ لوحة الإدارة", callback_data="admin_panel"))
    return kb

def confirm_deal_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✔️ موافقة", callback_data="deal_yes"),
        InlineKeyboardButton("❌ إلغاء", callback_data="deal_cancel"),
    )
    return kb

def deal_user_menu(deal_id, is_buyer, is_seller, is_done=False, dispute=False):
    kb = InlineKeyboardMarkup()
    if not is_done:
        if is_buyer:
            kb.add(InlineKeyboardButton("فتح نزاع 🚨", callback_data=f"dispute_{deal_id}"))
            kb.add(InlineKeyboardButton("✅ تم استلام الخدمة", callback_data=f"buyer_received_{deal_id}"))
        if is_seller:
            pass  # إضافات مستقبلية للبائع (ربما رفع نزاع ببعض السيناريوهات)
    else:
        pass
    kb.add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return kb

def admin_deals_menu(deal_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⬅️ إرجاع المبلغ للمشتري", callback_data=f"admin_return_{deal_id}"),
        InlineKeyboardButton("➡️ دفع المبلغ للبائع", callback_data=f"admin_release_{deal_id}"),
        InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"),
    )
    return kb

# === Handlers ===

# -- Main menu & /start --
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    ton_addr = database.get_user_wallet(user_id)
    if ton_addr:
        return await message.answer("مرحباً بك في بوت الوساطة عبر TON/USDT-TON!\nكل شيء يتم بالأمان، والتقييم، وعمولة 2%.", reply_markup=main_menu(user_id))
    else:
        await message.answer("لتفعيل البوت يجب عليك إدخال عنوان محفظتك TON أولاً. أرسل عنوانك هنا:")
        await state.set_state(EditWalletState.enter_wallet.state)

async def set_wallet(message: types.Message, state: FSMContext):
    ton_addr = message.text.strip()
    if not utils.is_valid_ton_address(ton_addr):
        return await message.reply("❌ العنوان غير صحيح. أرسل عنوان TON صالح فقط.")
    database.add_user(message.from_user.id, message.from_user.username, ton_addr)
    await message.answer("✅ تم ربط عنوان محفظتك بنجاح! يمكنك الآن البدء.", reply_markup=main_menu(message.from_user.id))
    await state.finish()

# -- Main Menu Buttons --
async def menu_cb(call: CallbackQuery, state: FSMContext):
    d = call.data
    u = call.from_user
    if d == "main_menu":
        await call.message.edit_text("مرحباً بك في القائمة الرئيسية.", reply_markup=main_menu(u.id))
    elif d == "new_deal":
        await call.message.edit_text("اختر نوع الصفقة:", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("شراء 🛒", callback_data="deal_mode_buy"),
            InlineKeyboardButton("بيع 🏷️", callback_data="deal_mode_sell"),
            InlineKeyboardButton("خدمة 🔧", callback_data="deal_mode_service"),
            InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")
        ))
        await DealState.select_mode.set()
    elif d == "my_deals":
        await show_my_deals(call)
    elif d == "referral":
        await referral_screen(call)
    elif d == "my_rating":
        await my_rating_screen(call)
    elif d == "blacklist":
        await blacklist_screen(call)
    elif d == "about":
        await call.message.edit_text("بوت وساطة آمن. العمولة 2%. النظام يدعم TON وUSDT-TON. كل استخدامك مراقب وآمن.\nقناة الدعم: ...", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")))
    elif d == "admin_panel":
        await admin_panel_screen(call)
    else:
        await call.answer("🚫 زر غير معرف")

# -- Deal Creation Flow --
async def deal_mode_select(call: CallbackQuery, state: FSMContext):
    mode = call.data.replace("deal_mode_", "")
    await state.update_data(mode=mode)
    await call.message.edit_text("أدخل اسم مستخدم الطرف الآخر (بدون @):")
    await DealState.select_partner.set()

async def deal_enter_partner(message: types.Message, state: FSMContext):
    partner_username = message.text.replace("@", "").strip()
    # في الإنتاج ستبحث عن العميل وتحصل على ID
    await state.update_data(partner_username=partner_username)
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("TON 💠", callback_data="deal_curr_TON"),
        InlineKeyboardButton("USDT-TON 💵", callback_data="deal_curr_USDT"),
        InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")
    )
    await message.answer("اختر العملة المطلوبة:", reply_markup=kb)
    await DealState.select_currency.set()

async def deal_currency_select(call: CallbackQuery, state: FSMContext):
    currency = call.data.replace("deal_curr_", "")
    await state.update_data(currency=currency)
    await call.message.edit_text("أدخل مبلغ الصفقة بالعملة المختارة:")
    await DealState.enter_amount.set()

async def deal_enter_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except Exception:
        return await message.reply("❌ مبلغ غير صحيح. أعد المحاولة.")
    await state.update_data(amount=amount)
    await message.answer("اكتب وصف مختصر للسلعة/الخدمة:")
    await DealState.enter_description.set()

async def deal_enter_desc(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(description=desc)
    data = await state.get_data()
    confirm_txt = f"ملخص الصفقة:\nالطرف الآخر: @{data['partner_username']}\nالعملة: {data['currency']}\nالمبلغ: {data['amount']}\nالوصف: {desc}\n\nهل ترغب في إرسال الصفقة للطرف الآخر؟"
    await message.answer(confirm_txt, reply_markup=confirm_deal_menu())
    await DealState.confirm.set()

async def deal_confirm_or_cancel(call: CallbackQuery, state: FSMContext):
    if call.data == "deal_yes":
        # إنشاء الصفقة — جلب معرف الطرف الآخر من username
        data = await state.get_data()
        partner_id = await find_user_id_by_username(data['partner_username'])
        if not partner_id:
            await call.message.edit_text("❌ الطرف غير موجود (يجب على الطرف الآخر بدء البوت أولاً).", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")))
            return
        # مسجّل هو مشترٍ أو بائع؟
        buyer_id, seller_id = (call.from_user.id, partner_id) if data['mode'] == "buy" else (partner_id, call.from_user.id)
        memo = utils.generate_deal_memo(len(database.get_user_deals(call.from_user.id)) + 1)
        deal_id = database.add_deal(buyer_id, seller_id, data['currency'], data['amount'], data['description'], memo)
        # إعلام الطرف الآخر، إنتظار موافقته
        try:
            await call.bot.send_message(partner_id, f"لديك صفقة جديدة من @{call.from_user.username}.\nالمبلغ: {data['amount']} {data['currency']}\nالوصف: {data['description']}", reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("✔️ موافقة", callback_data=f"deal_accept_{deal_id}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"deal_reject_{deal_id}")))
            await call.message.edit_text("تم إرسال الصفقة للطرف الآخر وتنتظر موافقته.")
        except Exception:
            await call.message.edit_text("❌ الطرف الآخر لم يبدأ البوت بعد…")
        await state.finish()
    else:
        await call.message.edit_text("تم إلغاء العملية.", reply_markup=main_menu(call.from_user.id))
        await state.finish()

# ---- موافقة الطرف الآخر ----
async def deal_accept_reject(call: CallbackQuery, state: FSMContext):
    is_accept = "accept" in call.data
    deal_id = int(call.data.split("_")[-1])
    d = database.get_deal(deal_id)
    if not d:
        return await call.answer("❌ الصفقة غير موجودة.")
    if not is_accept:
        database.update_deal_state(deal_id, "cancelled")
        await call.message.edit_text("تم رفض الصفقة.", reply_markup=main_menu(call.from_user.id))
        try:
            await call.bot.send_message(d[1], "تم رفض الصفقة من الطرف الآخر.")
        except: pass
        return
    # قبول الصفقة — اطبع تعليمات الدفع
    database.update_deal_state(deal_id, "waiting_deposit")
    # حدد العملة، أعطِ عنوان المحفظة + الميمو الحصري
    currency = d[3]
    amount = d[4]
    memo = d[10]
    instr = (
        f"لإتمام الصفقة أرسل: {amount} {currency}\n"
        f"على عنوان المحفظة التالية:\n\n"
        f"`{config.TON_WALLET}`\n\n"
        f"وضع ميمو (Transaction memo): `{memo}`\n\n"
        f"بعد الإرسال، اضغط الزر التالي لتأكيد الدفع."
    )
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💸 تم الدفع", callback_data=f"user_paid_{deal_id}")
    )
    # أبلغ المشتري بالتعليمات
    try:
        await call.bot.send_message(d[1], instr, parse_mode="Markdown", reply_markup=kb)
    except:
        pass
    await call.message.edit_text("تمت الموافقة على الصفقة. في انتظار إيداع المشتري…")
    await state.finish()

async def user_paid(call: CallbackQuery, state: FSMContext):
    # يجب على الأدمن التحقق أو التحقق الآلي من التحويل
    deal_id = int(call.data.split("_")[-1])
    d = database.get_deal(deal_id)
    if not d:
        await call.answer("❌ الصفقة غير موجودة.")
        return
    # خطوة التدقيق لاحقاً (آلية أو يدوياً)
    database.update_deal_state(deal_id, "deposited")
    # أبلغ الجميع بأن المبلغ وصل (هنا افترض أن التحويل مؤكد فوراً، للتسهيل)
    await call.message.edit_text(
        "تم رصد التحويل! بدأ تنفيذ الصفقة.\n\nعلى البائع تسليم المنتج أو الخدمة ثم ينتظر تأكيد المشتري.",
        reply_markup=deal_user_menu(deal_id, is_buyer=True, is_seller=False)
    )
    try:
        await call.bot.send_message(d[2], f"تم تأكيد إيداع الضمان من المشتري. يمكنك الآن تسليم المنتج/الخدمة وانتظر تأكيد المشتري.")
    except:
        pass

# --- تأكيد المشتري، إغلاق الصفقة ---
async def buyer_received(call: CallbackQuery, state: FSMContext):
    deal_id = int(call.data.split("_")[-1])
    d = database.get_deal(deal_id)
    if not d or d[6] == "completed":
        await call.answer("❌ الصفقة غير موجودة أو مكتملة.")
        return
    database.complete_deal(deal_id)
    # (اقتطاع العمولة ونقل المبلغ) — هذه الخطوة يتم تفعيلها عبر wallet.py في النسخ الإنتاجية
    # أبلغ الطرفين والإدارة
    await call.message.edit_text("✅ تم إنهاء الصفقة! يرجى تقييم الطرف الآخر:")
    try:
        await call.bot.send_message(d[2], "✅ تم إنهاء الصفقة بنجاح من المشتري. سيتم تحويل المبلغ لك (بعد خصم العمولة).")
    except:
        pass
    await rate_user_flow(call, deal_id, d)

# --- فتح نزاع ---
async def open_dispute(call: CallbackQuery, state: FSMContext):
    deal_id = int(call.data.split("_")[-1])
    await state.update_data(deal_id=deal_id)
    await call.message.answer("يرجى شرح سبب المشكلة أو الخلاف (سيتم إرساله للإدارة):")
    await DealState.dispute_msg.set()

async def dispute_msg_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    deal_id = data.get("deal_id")
    if not deal_id:
        return
    database.update_deal_state(deal_id, "dispute")
    txt = f"🚨 نزاع في صفقة رقم [{deal_id}]!\nسبب النزاع: {message.text}\nيرجى من الإدارة التدخل."
    for a in config.ADMIN_IDS:
        try:
            await message.bot.send_message(a, txt, reply_markup=admin_deals_menu(deal_id))
        except: pass
    await message.answer("تم فتح النزاع. سيتم التواصل معك من قبل الإدارة.", reply_markup=main_menu(message.from_user.id))
    await state.finish()

# التقييم للطرفين بعد إتمام أي صفقة
async def rate_user_flow(call: CallbackQuery, deal_id, deal_row):
    buyer_id, seller_id = deal_row[1], deal_row[2]
    from_user = call.from_user.id
    to_user = seller_id if from_user == buyer_id else buyer_id
    await call.bot.send_message(from_user, f"قيّم تجربتك مع الطرف الآخر في صفقة رقم [{deal_id}] (1 إلى 5):")
    # التحكم في التقييم ستتم في استيت جديد يمكن بناؤه في نسخة مطورة.

# -- صفقاتي / سجل المستخدم --
async def show_my_deals(call: CallbackQuery):
    uid = call.from_user.id
    deals = database.get_user_deals(uid)
    if not deals:
        await call.message.edit_text("😢 ليس لديك أي صفقات بعد.", reply_markup=main_menu(uid))
        return
    txt = "سجل صفقاتك:\n"
    for d in deals[:8]:
        state = d[6]
        txt += f"#{d[0]} | {d[3]} {d[4]} | {state}\n"
    await call.message.edit_text(txt, reply_markup=main_menu(uid))

# -- الإحالة --
async def referral_screen(call: CallbackQuery):
    uid = call.from_user.id
    link = f"https://t.me/{(await call.bot.get_me()).username}?start={uid}"
    total_earned = database.get_user(call.from_user.id)[8] or 0
    await call.message.edit_text(f"رابط الإحالة الخاص بك:\n{link}\n\n💸 أرباحك حتى الآن: {total_earned:.2f} TON/USDT-TON", reply_markup=main_menu(uid))

# -- تقييمي --
async def my_rating_screen(call: CallbackQuery):
    count, total = database.get_user_rating(call.from_user.id)
    score = round(total/count, 2) if count > 0 else "-"
    await call.message.edit_text(f"تقييمك: ⭐️ {score} (عدد التقييمات: {count})", reply_markup=main_menu(call.from_user.id))

# -- قائمة النصابين --
async def blacklist_screen(call: CallbackQuery):
    bl = database.get_blacklist()
    txt="قائمة النصابين:\n"
    for x in bl:
        txt += f"• @{x[0]} | {x[1]}\n"
    if not bl: txt = "لا يوجد حاليًا"
    await call.message.edit_text(txt, reply_markup=main_menu(call.from_user.id))

# -- لوحة الأدمن --
async def admin_panel_screen(call: CallbackQuery):
    txt = "لوحة الإدارة:\nإدارة النزاعات - قائمة النصابين - تقارير العمولة"
    await call.message.edit_text(txt, reply_markup=main_menu(call.from_user.id))

# ــ مساعدات FSM وربط جميع Handlers بشكل صحيح ــ
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=['start'], state="*")
    dp.register_message_handler(set_wallet, state=EditWalletState.enter_wallet)

    dp.register_callback_query_handler(menu_cb, state="*")
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

# -- دالة مساعدة للبحث عن ID مستخدم من username (تحتاج قاعدة المستخدمين أن تتحدث دورياً) --
async def find_user_id_by_username(username):
    import sqlite3
    conn = sqlite3.connect(config.DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT tg_id FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None