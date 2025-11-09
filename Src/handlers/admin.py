from aiogram import types, Dispatcher
from ..database import get_deals_by_state, get_admin_earnings, update_deal_state, get_deal, set_deal_tx_hash, complete_deal
from .menu import main_menu
from ..wallet import send_ton

async def admin_panel_screen(call: types.CallbackQuery):
    earnings = get_admin_earnings()
    txt = f"لوحة الإدارة\nإجمالي الأرباح: {earnings:.2f} TON\n"
    disputes = get_deals_by_state("dispute")
    txt += f"\nصفقات النزاع ({len(disputes)}):"
    for d in disputes[:10]:
        txt += f"\n#{d[0]} | {d[3]} {d[4]} | {d[6]}"
    await call.message.edit_text(txt, reply_markup=main_menu(call.from_user.id))

async def admin_handle_deal(call: types.CallbackQuery):
    cb = call.data
    deal_id = int(cb.split("_")[-1])
    d = get_deal(deal_id)
    if not d:
        await call.answer("❌ الصفقة غير موجودة.")
        return
    buyer_addr = d[1]
    seller_addr = d[2]
    amount = d[4]
    if "admin_return" in cb:
        addr = buyer_addr
    else:
        addr = seller_addr
    txid = await send_ton(addr, amount)
    set_deal_tx_hash(deal_id, str(txid))
    complete_deal(deal_id)
    update_deal_state(deal_id, "completed")
    await call.message.answer("تمت تسوية الصفقة وتحويل المبلغ.", reply_markup=main_menu(call.from_user.id))

def register(dp: Dispatcher):
    dp.register_callback_query_handler(admin_panel_screen, lambda c: c.data == "admin_panel")
    dp.register_callback_query_handler(admin_handle_deal, lambda c: c.data.startswith("admin_return_") or c.data.startswith("admin_release_"))