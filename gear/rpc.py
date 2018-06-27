import sys
import json
import logging
import traceback
from .thor.client import thor
from .utils.compat import noop
from .utils.types import (
    normalize_number,
    normalize_block_identifier,
    force_obj_to_text,
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


FILTER_KWARGS_MAP = {
    'fromBlock': 'from_block',
    'toBlock': 'to_block',
}


FILTER_FORMATTERS = {
    'fromBlock': normalize_block_identifier,
    'toBlock': normalize_block_identifier,
}


def input_filter_params_formatter(filter_params):
    return {
        FILTER_KWARGS_MAP.get(k, k): FILTER_FORMATTERS.get(k, noop)(v)
        for k, v in filter_params.items()
    }


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
