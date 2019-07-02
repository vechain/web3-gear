import rlp
import uuid
from gear.utils.singleton import Singleton
from gear.utils.types import (
    encode_number,
    encode_hex,
    strip_0x
)
from gear.utils.compat import (
    thor_block_convert_to_eth_block,
    thor_receipt_convert_to_eth_receipt,
    thor_tx_convert_to_eth_tx,
    thor_log_convert_to_eth_log,
    thor_storage_convert_to_eth_storage,
    ThorTransaction,
    intrinsic_gas,
)
from .request import (
    Restful,
    get,
    post,
)


def _attribute(obj, key): return None if obj is None else obj[key]


class ThorClient(object, metaclass=Singleton):
    def __init__(self):
        self.filter = {}

    def set_endpoint(self, endpoint):
        restful = Restful(endpoint)
        self.transactions = restful.transactions
        self.blocks = restful.blocks
        self.accounts = restful.accounts
        self.events = restful.events
        self.debug = restful.debug

    def set_accounts(self, account_manager):
        self.account_manager = account_manager

    async def trace_transaction(self, tx_hash):
        tx = await self.transactions(tx_hash).make_request(get)
        if tx is None:
            return None
        data = {
            "name": "",
            "target": "{}/{}/0".format(tx["meta"]["blockID"], tx_hash)
        }
        return await self.debug.tracers.make_request(post, data=data)

    async def get_storage_at(self, address, position, block_identifier):
        params = {
            "revision": block_identifier
        }
        storage = await self.accounts(address).storage(
            position).make_request(get, params=params)
        return _attribute(storage, "value")

    async def storage_range_at(self, blk_hash, tx_index, contract_addr, key_start, max_result):
        data = {
            "Address": contract_addr,
            "KeyStart": key_start,
            "MaxResult": max_result,
            "target": "{}/{}/0".format(blk_hash, tx_index)
        }
        result = await self.debug("storage-range").make_request(post, data=data)
        if result is None:
            return None
        result["storage"] = thor_storage_convert_to_eth_storage(
            result["storage"])
        return result

    def get_accounts(self):
        return self.account_manager.get_accounts()

    async def get_block_number(self):
        blk = await self.blocks("best").make_request(get)
        return _attribute(blk, "number")

    async def get_block_id(self, block_identifier):
        blk = await self.blocks(block_identifier).make_request(get)
        return _attribute(blk, "id")

    async def estimate_gas(self, transaction):
        data = {
            "data": transaction["data"],
            "value": (encode_number(transaction.get("value", 0))).decode("utf-8"),
            "caller": transaction.get("from", None),
        }
        result = await self.accounts(transaction.get(
            "to", None)).make_request(post, data=data)
        if result is None or result["reverted"]:
            raise ValueError("Gas estimation failed.")
        return int(result["gasUsed"] * 1.2) + intrinsic_gas(transaction)

    async def call(self, transaction, block_identifier):
        params = {
            "revision": block_identifier,
        }
        data = {
            "data": transaction["data"],
            "value": (encode_number(transaction.get("value", 0))).decode("utf-8"),
            "caller": transaction.get("from", None),
        }
        result = await self.accounts(transaction.get("to", None)).make_request(
            post, data=data, params=params)
        return _attribute(result, "data")

    async def send_transaction(self, transaction):
        chain_tag = int((await thor.get_block(0))["hash"][-2:], 16)
        blk_ref = int(strip_0x((await thor.get_block("best"))["hash"])[:8], 16)
        tx = ThorTransaction(chain_tag, blk_ref, transaction)
        tx.sign(self.account_manager.get_priv_by_addr(transaction["from"]))
        raw = "0x{}".format(encode_hex(rlp.encode(tx)))
        return await self.send_raw_transaction(raw)

    async def send_raw_transaction(self, raw):
        data = {
            "raw": raw
        }
        result = await self.transactions.make_request(post, data=data)
        return _attribute(result, "id")

    async def get_transaction_by_hash(self, tx_hash):
        tx = await self.transactions(tx_hash).make_request(get)
        return None if tx is None else thor_tx_convert_to_eth_tx(tx)

    async def get_balance(self, address, block_identifier):
        params = {
            "revision": block_identifier
        }
        accout = await self.accounts(address).make_request(get, params=params)
        return _attribute(accout, "balance")

    async def get_transaction_receipt(self, tx_hash):
        receipt = await self.transactions(tx_hash).receipt.make_request(get)
        return None if receipt is None else thor_receipt_convert_to_eth_receipt(receipt)

    async def get_block(self, block_identifier):
        blk = await self.blocks(block_identifier).make_request(get)
        return None if blk is None else thor_block_convert_to_eth_block(blk)

    async def get_code(self, address, block_identifier):
        params = {
            "revision": block_identifier
        }
        code = await self.accounts(address).code.make_request(get, params=params)
        return _attribute(code, "code")

    def new_block_filter(self):
        filter_id = "0x{}".format(uuid.uuid4().hex)
        self.filter[filter_id] = BlockFilter(self)
        return filter_id

    def uninstall_filter(self, filter_id):
        if filter_id in self.filter:
            del self.filter[filter_id]
        return True

    def get_filter_changes(self, filter_id):
        func = self.filter.get(filter_id, lambda: [])
        return func()

    async def get_logs(self, address, query):
        params = {
            "address": address
        }
        logs = await self.events.make_request(post, data=query, params=params)
        result = thor_log_convert_to_eth_log(address, logs)
        return result


class BlockFilter(object):

    def __init__(self, client):
        super(BlockFilter, self).__init__()
        self.current = client.get_block_number()
        self.client = client

    def __call__(self):
        result = []
        best_num = self.client.get_block_number()
        if best_num:
            result = [
                id
                for id in map(self.client.get_block_id, range(self.current, best_num + 1))
                if id is not None
            ]
            self.current = best_num + 1
        return result


thor = ThorClient()
