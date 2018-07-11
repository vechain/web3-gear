import rlp
import uuid
from gear.utils.singleton import Singleton
from gear.utils.types import (
    encode_number,
    encode_hex,
    force_obj_to_bytes,
)
from gear.utils.compat import (
    thor_block_convert_to_eth_block,
    thor_receipt_convert_to_eth_receipt,
    thor_tx_convert_to_eth_tx,
    thor_log_convert_to_eth_log,
    ThorTransaction,
    intrinsic_gas,
)
from .request import (
    make_request,
    get,
    post,
)


class ThorClient(object, metaclass=Singleton):
    def __init__(self):
        self.account = lambda address: make_request("{0}/accounts/{1}".format(self.endpoint, address))\
            if address else\
            make_request("{0}/accounts".format(self.endpoint))
        self.transaction = lambda id: make_request("{0}/transactions/{1}".format(self.endpoint, id)) \
            if id else \
            make_request("{0}/transactions".format(self.endpoint))
        self.receipt = lambda id: make_request("{0}/transactions/{1}/receipt".format(self.endpoint, id))
        self.code = lambda address: make_request("{0}/accounts/{1}/code".format(self.endpoint, address))
        self.trace = lambda id: make_request("{0}/transactions/{1}/trace".format(self.endpoint, id))
        self.block = lambda revision: make_request("{0}/blocks/{1}".format(self.endpoint, revision))
        self.events = lambda: make_request("{0}/events".format(self.endpoint))
        self.filter = {}

    def set_endpoint(self, endpoint):
        self.endpoint = endpoint

    def set_accounts(self, account_manager):
        self.account_manager = account_manager

    def trace_transaction(self, tx_hash, params):
        if "fullStorage" in params:  # this option is not supported in thor.
            del params["fullStorage"]
        data = {
            "logConfig": params,
        }
        return self.trace(tx_hash)(post, data=data)

    def storage_range_at(self, blk_hash, tx_index, contract_addr, key_start):
        '''
        TODO
        '''
        raise Exception("Did not implement this interface.")

    def get_accounts(self):
        return self.account_manager.get_accounts()

    def get_block_number(self):
        block = self.block("best")(get)
        return None if block is None else block["number"]

    def get_block_id(self, block_identifier):
        blk = self.block(block_identifier)(get)
        return None if blk is None else blk["id"]

    def estimate_gas(self, transaction):
        if "to" not in transaction:
            to_addr = None
        else:
            to_addr = transaction["to"]
        data = {
            "data": transaction["data"],
            "value": (encode_number(transaction.get("value", 0))).decode("utf-8"),
            "caller": transaction["from"],
        }
        result = self.account(to_addr)(post, data=data)
        if result is None:
            return encode_number(0)
        return encode_number(int(result["gasUsed"] * 1.2) + intrinsic_gas(transaction))

    def call(self, transaction, block_identifier):
        params = {
            "revision": block_identifier,
        }
        data = {
            "data": transaction["data"],
            "value": (encode_number(transaction.get("value", 0))).decode("utf-8"),
        }
        result = self.account(transaction.get("to", None))(post, data=data, params=params)
        return None if result is None else result["data"]

    def send_transaction(self, transaction):
        tx = ThorTransaction(self, transaction)
        tx.sign(self.account_manager.get_priv_by_addr(force_obj_to_bytes(transaction["from"])))
        data = {
            "raw": "0x{}".format(encode_hex(rlp.encode(tx)))
        }
        result = self.transaction(None)(post, data=data)
        return None if result is None else result["id"]

    def get_transaction_by_hash(self, tx_hash):
        tx = self.transaction(tx_hash)(get)
        return None if tx is None else thor_tx_convert_to_eth_tx(tx)

    def get_balance(self, address, block_identifier):
        params = {
            "revision": block_identifier
        }
        accout = self.account(address)(get, params=params)
        return None if accout is None else accout["balance"]

    def get_transaction_receipt(self, tx_hash):
        receipt = self.receipt(tx_hash)(get)
        return None if receipt is None else thor_receipt_convert_to_eth_receipt(receipt)

    def get_block(self, block_identifier):
        blk = self.block(block_identifier)(get)
        return None if blk is None else thor_block_convert_to_eth_block(blk)

    def get_code(self, address, block_identifier):
        params = {
            "revision": block_identifier
        }
        code = self.code(address)(get, params=params)
        return None if code is None else code["code"]

    def new_block_filter(self):
        filter_id = uuid.uuid1().__str__()
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
        logs = self.events()(post, data=query, params=params)
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
            self.current = best_num
        return result


thor = ThorClient()
