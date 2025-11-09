from aiogram.dispatcher.filters.state import State, StatesGroup

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