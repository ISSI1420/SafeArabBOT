from ton import TonlibClient
import config
import asyncio

client = None

def get_client():
    global client
    if client is None:
        client = TonlibClient(ls_index=None, config_path=None)
    return client

async def send_ton(destination: str, amount: float, comment: str = ""):
    c = get_client()
    await c.init()
    await c.import_key(config.TON_SEED.split())
    result = await c.transfer(
        to_addr=destination,
        amount=int(amount * 1e9),
        message=comment
    )
    return result['txid']