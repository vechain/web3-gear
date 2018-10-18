import rlp
import uuid
from gear.utils.singleton import Singleton
from gear.utils.types import (
    encode_number,
    encode_hex
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

    def trace_transaction(self, tx_hash):
        tx = self.transactions(tx_hash).make_request(get)
        if tx is None:
            return None
        data = {
            "name": "",
            "target": "{}/{}/0".format(tx["meta"]["blockID"], tx_hash)
        }
        return self.debug.tracers.make_request(post, data=data)

    def storage_range_at(self, blk_hash, tx_index, contract_addr, key_start, max_result):
        data = {
            "ContractAddress": contract_addr,
            "KeyStart": key_start,
            "MaxResult": max_result,
            "target": "{}/{}/0".format(blk_hash, tx_index)
        }
        result = self.debug.storage.make_request(post, data=data)
        if result is None:
            return None
        result["storage"] = thor_storage_convert_to_eth_storage(result["storage"])
        return result

    def get_accounts(self):
        return self.account_manager.get_accounts()

    def get_block_number(self):
        blk = self.blocks("best").make_request(get)
        return _attribute(blk, "number")

    def get_block_id(self, block_identifier):
        blk = self.blocks(block_identifier).make_request(get)
        return _attribute(blk, "id")

    def estimate_gas(self, transaction):
        data = {
            "data": transaction["data"],
            "value": (encode_number(transaction.get("value", 0))).decode("utf-8"),
            "caller": transaction.get("from", None),
        }
        result = self.accounts(transaction.get("to", None)).make_request(post, data=data)
        if result is None:
            return 0
        return int(result["gasUsed"] * 1.2) + intrinsic_gas(transaction)

    def call(self, transaction, block_identifier):
        params = {
            "revision": block_identifier,
        }
        data = {
            "data": transaction["data"],
            "value": (encode_number(transaction.get("value", 0))).decode("utf-8"),
            "caller": transaction.get("from", None),
        }
        result = self.accounts(transaction.get("to", None)).make_request(post, data=data, params=params)
        return _attribute(result, "data")

    def send_transaction(self, transaction):
        tx = ThorTransaction(self, transaction)
        tx.sign(self.account_manager.get_priv_by_addr(transaction["from"]))
        data = {
            "raw": "0x{}".format(encode_hex(rlp.encode(tx)))
        }
        result = self.transactions.make_request(post, data=data)
        return _attribute(result, "id")

    def get_transaction_by_hash(self, tx_hash):
        tx = self.transactions(tx_hash).make_request(get)
        return None if tx is None else thor_tx_convert_to_eth_tx(tx)

    def get_balance(self, address, block_identifier):
        params = {
            "revision": block_identifier
        }
        accout = self.accounts(address).make_request(get, params=params)
        return _attribute(accout, "balance")

    def get_transaction_receipt(self, tx_hash):
        receipt = self.transactions(tx_hash).receipt.make_request(get)
        return None if receipt is None else thor_receipt_convert_to_eth_receipt(receipt)

    def get_block(self, block_identifier):
        blk = self.blocks(block_identifier).make_request(get)
        return None if blk is None else thor_block_convert_to_eth_block(blk)

    def get_code(self, address, block_identifier):
        params = {
            "revision": block_identifier
        }
        code = self.accounts(address).code.make_request(get, params=params)
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

    def get_logs(self, address, query):
        params = {
            "address": address
        }
        logs = self.events.make_request(post, data=query, params=params)
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
