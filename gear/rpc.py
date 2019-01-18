import itertools
import json
import logging
import sys
import traceback
from jsonrpc import JSONRPCResponseManager, Dispatcher
from werkzeug.wrappers import Request, Response
from .thor.client import thor
from .utils.compat import noop
from .utils.types import (
    encode_number,
    force_obj_to_text,
    normalize_block_identifier,
    normalize_number
)


logging.basicConfig(
    level=logging.INFO,
    format='received rpc request - %(message)s',
)
logger = logging.getLogger(__name__)


class RichDispatcher(Dispatcher):
    """
    输出 Method not found 错误信息
    """

    def __getitem__(self, key):
        logInfo = key
        if key not in self.method_map:
            logInfo = "{}, but method not found".format(key)
        logger.info(logInfo)
        return self.method_map[key]


dispatcher = RichDispatcher()


#
# formatter
#
TXN_FORMATTERS = {
    'value': normalize_number,
    'gas': normalize_number,
}


def input_transaction_formatter(transaction):
    return {
        k: TXN_FORMATTERS.get(k, noop)(v)
        for k, v in transaction.items()
    }


def input_log_filter_formatter(filter_params):
    params_range = {"unit": "block"}
    params_range["from"] = int(filter_params["fromBlock"], 16)
    to_blk = filter_params.get("toBlock", None)
    if to_blk:
        params_range["to"] = int(to_blk, 16)
    return {
        "range": params_range,
        "topicSets": topics_formatter(filter_params.get("topics", []))
    }


def topics_formatter(eth_topics):
    if eth_topics:
        matrix = [x if isinstance(x, list) else [x] for x in eth_topics]
        return [
            {
                "topic{}".format(index): topic
                for index, topic in enumerate(e)
            }
            for e in itertools.product(*matrix)
        ]
    return []


#
#
#
@dispatcher.add_method
def rpc_modules():
    return {
        "eth": "1.0",
        "net": "1.0",
        "web3": "1.0",
    }


#
# debug
#
@dispatcher.add_method
def debug_traceTransaction(tx_hash, params):
    return thor.trace_transaction(tx_hash)


@dispatcher.add_method
def debug_storageRangeAt(blk_hash, tx_index, contract_addr, key_start, max_result):
    return thor.storage_range_at(blk_hash, tx_index, contract_addr, key_start, max_result)


#
# net_api
#
@dispatcher.add_method
def net_version():
    return 5777


@dispatcher.add_method
def net_listening():
    return False


#
# evm_api
# 没有真实实现, 只是为了实现接口
#

@dispatcher.add_method
def evm_snapshot():
    return encode_number(0)


@dispatcher.add_method
def evm_revert(snapshot_idx=None):
    return True


#
# web3
#
@dispatcher.add_method
def web3_clientVersion():
    from . import __version__
    return "Web3-Gear/" + __version__ + "/{platform}/python{v.major}.{v.minor}.{v.micro}".format(
        v=sys.version_info,
        platform=sys.platform,
    )


#
# eth_api
#
@dispatcher.add_method
def eth_getStorageAt(address, position, block_identifier="best"):
    if position.startswith("0x"):
        position = position[2:]
    position = "0x{}".format(position.zfill(64))
    return thor.get_storage_at(
        address, position, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_getTransactionCount(address, block_identifier="best"):
    '''
    ethereum 用来处理 nonce, Thor 不需要
    '''
    return encode_number(0)


@dispatcher.add_method
def eth_accounts():
    return thor.get_accounts()


@dispatcher.add_method
def eth_getCode(address, block_identifier="best"):
    return thor.get_code(address, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_blockNumber():
    return encode_number(thor.get_block_number())


@dispatcher.add_method
def eth_estimateGas(transaction):
    formatted_transaction = input_transaction_formatter(transaction)
    return encode_number(thor.estimate_gas(formatted_transaction))


@dispatcher.add_method
def eth_call(transaction, block_identifier="best"):
    formatted_transaction = input_transaction_formatter(transaction)
    return thor.call(formatted_transaction, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_sendTransaction(transaction):
    '''
    发送未签名的交易
    '''
    formatted_transaction = input_transaction_formatter(transaction)
    return thor.send_transaction(formatted_transaction)


@dispatcher.add_method
def eth_getBalance(address, block_identifier="best"):
    return thor.get_balance(address, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_getTransactionByHash(tx_hash):
    try:
        return thor.get_transaction_by_hash(tx_hash)
    except Exception:
        traceback.print_exc()
        return None


@dispatcher.add_method
def eth_getTransactionReceipt(tx_hash):
    try:
        return thor.get_transaction_receipt(tx_hash)
    except Exception:
        traceback.print_exc()
        return None


@dispatcher.add_method
def eth_getBlockByHash(block_hash, full_tx=False):
    return get_block(block_hash, full_tx)


@dispatcher.add_method
def eth_getBlockByNumber(block_number, full_tx=False):
    return get_block(block_number, full_tx)


def get_block(block_identifier, full_tx):
    blk = thor.get_block(normalize_block_identifier(block_identifier))
    if blk and full_tx:
        blk["transactions"] = [eth_getTransactionByHash(
            tx) for tx in blk["transactions"]]
    return blk


@dispatcher.add_method
def eth_newBlockFilter():
    return thor.new_block_filter()


@dispatcher.add_method
def eth_uninstallFilter(filter_id):
    return thor.uninstall_filter(filter_id)


@dispatcher.add_method
def eth_getFilterChanges(filter_id):
    return thor.get_filter_changes(filter_id)


@dispatcher.add_method
def eth_getLogs(filter_obj):
    return thor.get_logs(filter_obj.get("address", None), input_log_filter_formatter(filter_obj))


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(
        request.data,
        dispatcher,
    )
    response = Response(
        json.dumps(force_obj_to_text(response.data, True)),
        headers={
            "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept",
            "Access-Control-Allow-Origin": "*",
        },
        mimetype='application/json',
    )
    return response
