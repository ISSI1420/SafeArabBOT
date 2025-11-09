import re

def is_valid_ton_address(address: str):
    return bool(re.match(r"^[A-Za-z0-9\-_]{48,66}$", address.strip()))

def generate_deal_memo(deal_id: int) -> str:
    return f"DEAL{deal_id}"