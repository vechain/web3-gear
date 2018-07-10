import sys
import json
import uuid
import logging
import traceback
import itertools
from .thor.client import thor
from .utils.compat import noop
from .utils.types import (
    normalize_number,
    normalize_block_identifier,
    force_obj_to_text,
    encode_number,
)
from jsonrpc import (
    JSONRPCResponseManager,
    dispatcher,
)
from werkzeug.wrappers import (
    Request,
    Response,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s[line:%(lineno)d] - received rpc request - %(message)s',
)
logger = logging.getLogger(__name__)


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
    logger.info('debug_traceTransaction')
    return thor.trace_transaction(tx_hash, params)


@dispatcher.add_method
def debug_storageRangeAt(blk_hash, tx_index, contract_addr, key_start):
    logger.info('debug_storageRangeAt')
    return thor.storage_range_at(blk_hash, tx_index, contract_addr, key_start)


#
# net_api
#
@dispatcher.add_method
def net_version():
    return 1


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
def eth_accounts():
    logger.info('eth_accounts')
    return thor.get_accounts()


@dispatcher.add_method
def eth_getCode(address, block_identifier="best"):
    logger.info('eth_getCode')
    return thor.get_code(address, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_blockNumber():
    logger.info('eth_blockNumber')
    return thor.get_block_number()


@dispatcher.add_method
def eth_estimateGas(transaction):
    logger.info('eth_estimateGas')
    formatted_transaction = input_transaction_formatter(transaction)
    return thor.estimate_gas(formatted_transaction)


@dispatcher.add_method
def eth_call(transaction, block_identifier="best"):
    logger.info('eth_call')
    formatted_transaction = input_transaction_formatter(transaction)
    return thor.call(formatted_transaction, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_sendTransaction(transaction):
    '''
    发送未签名的交易
    '''
    logger.info('eth_sendTransaction')
    formatted_transaction = input_transaction_formatter(transaction)
    return thor.send_transaction(formatted_transaction)


@dispatcher.add_method
def eth_getBalance(address, block_identifier="best"):
    logger.info('eth_getBalance')
    return thor.get_balance(address, normalize_block_identifier(block_identifier))


@dispatcher.add_method
def eth_getTransactionByHash(tx_hash):
    logger.info('eth_getTransactionByHash')
    try:
        return thor.get_transaction_by_hash(tx_hash)
    except Exception:
        traceback.print_exc()
        return None


@dispatcher.add_method
def eth_getTransactionReceipt(tx_hash):
    logger.info('eth_getTransactionReceipt')
    try:
        return thor.get_transaction_receipt(tx_hash)
    except Exception:
        traceback.print_exc()
        return None


@dispatcher.add_method
def eth_getBlockByHash(block_hash, full_tx=True):
    '''
    full_tx 该参数仅为了与以太坊兼容, thor 中无用
    '''
    logger.info('eth_getBlockByHash')
    return thor.get_block(normalize_block_identifier(block_hash))


@dispatcher.add_method
def eth_getBlockByNumber(block_number, full_tx=True):
    '''
    full_tx 该参数仅为了与以太坊兼容, thor 中无用
    '''
    logger.info('eth_getBlockByNumber')
    return thor.get_block(normalize_block_identifier(block_number))


@dispatcher.add_method
def eth_newBlockFilter():
    logger.info('eth_newBlockFilter')
    filter_id = uuid.uuid1().__str__()
    current = thor.get_block_number()
    thor.filter[filter_id] = lambda: thor.get_blocks_after_num(current)
    return filter_id


@dispatcher.add_method
def eth_uninstallFilter(filter_id):
    logger.info('eth_uninstallFilter')
    del thor.filter[filter_id]
    return None


@dispatcher.add_method
def eth_getFilterChanges(filter_id):
    logger.info('eth_getFilterChanges')
    filter_func = thor.filter.get(filter_id, lambda: None)
    return filter_func()


@dispatcher.add_method
def eth_getLogs(filter_obj):
    logger.info('eth_getLogs')
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
