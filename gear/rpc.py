import itertools
import functools
import logging
import sys
import json
import traceback
from .thor.client import thor
from .utils.compat import noop
from .utils.types import (
    encode_number,
    force_obj_to_text,
    normalize_block_identifier,
    normalize_number
)
from jsonrpcserver import method


def async_serialize(func):
    @functools.wraps(func)
    async def wrapper(*args, **kw):
        try:
            result = await func(*args, **kw)
            if isinstance(result, str):
                return result
            return force_obj_to_text(result, True)
        except Exception as e:
            traceback.print_exc()
            raise e
    return wrapper


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
@method
async def rpc_modules():
    return {
        "eth": "1.0",
        "net": "1.0",
        "web3": "1.0",
    }


#
# debug
#
@method
@async_serialize
async def debug_traceTransaction(tx_hash, params):
    return await thor.trace_transaction(tx_hash)


@method
@async_serialize
async def debug_storageRangeAt(blk_hash, tx_index, contract_addr, key_start, max_result):
    return await thor.storage_range_at(blk_hash, tx_index, contract_addr, key_start, max_result)


#
# net_api
#
@method
async def net_version():
    return 5777


@method
async def net_listening():
    return False


#
# evm_api
# 没有真实实现, 只是为了实现接口
#

@method
async def evm_snapshot():
    return encode_number(0)


@method
async def evm_revert(snapshot_idx=None):
    return True


#
# web3
#
def make_version():
    from . import __version__
    return "Web3-Gear/" + __version__ + "/{platform}/python{v.major}.{v.minor}.{v.micro}".format(
        v=sys.version_info,
        platform=sys.platform,
    )


@method
async def web3_clientVersion():
    return make_version()


#
# eth_api
#
@method
@async_serialize
async def eth_getStorageAt(address, position, block_identifier="best"):
    if position.startswith("0x"):
        position = position[2:]
    position = "0x{}".format(position.zfill(64))
    return await thor.get_storage_at(
        address, position, normalize_block_identifier(block_identifier))


@method
async def eth_getTransactionCount(address, block_identifier="best"):
    '''
    ethereum 用来处理 nonce, Thor 不需要
    '''
    return encode_number(0)


@method
async def eth_accounts():
    return thor.get_accounts()


@method
@async_serialize
async def eth_getCode(address, block_identifier="best"):
    return await thor.get_code(address, normalize_block_identifier(block_identifier))


@method
@async_serialize
async def eth_blockNumber():
    return encode_number(await thor.get_block_number())


@method
@async_serialize
async def eth_estimateGas(transaction):
    formatted_transaction = input_transaction_formatter(transaction)
    return encode_number(await thor.estimate_gas(formatted_transaction))


@method
@async_serialize
async def eth_call(transaction, block_identifier="best"):
    formatted_transaction = input_transaction_formatter(transaction)
    return await thor.call(formatted_transaction, normalize_block_identifier(block_identifier))


@method
@async_serialize
async def eth_sendTransaction(transaction):
    '''
    发送未签名的交易
    '''
    formatted_transaction = input_transaction_formatter(transaction)
    return await thor.send_transaction(formatted_transaction)


@method
@async_serialize
async def eth_sendRawTransaction(raw):
    '''
    发送已签名的交易
    '''
    return await thor.send_raw_transaction(raw)


@method
@async_serialize
async def eth_getBalance(address, block_identifier="best"):
    return await thor.get_balance(address, normalize_block_identifier(block_identifier))


@method
@async_serialize
async def eth_getTransactionByHash(tx_hash):
    if tx_hash:
        return await thor.get_transaction_by_hash(tx_hash)
    return None


@method
@async_serialize
async def eth_getTransactionReceipt(tx_hash):
    if tx_hash:
        return await thor.get_transaction_receipt(tx_hash)
    return None


@method
@async_serialize
async def eth_getBlockByHash(block_hash, full_tx=False):
    return await get_block(block_hash, full_tx)


@method
@async_serialize
async def eth_getBlockByNumber(block_number, full_tx=False):
    return await get_block(block_number, full_tx)


async def get_block(block_identifier, full_tx):
    blk = await thor.get_block(normalize_block_identifier(block_identifier))
    if blk and full_tx:
        blk["transactions"] = [eth_getTransactionByHash(
            tx) for tx in blk["transactions"]]
    return blk


@method
async def eth_newBlockFilter():
    return await thor.new_block_filter()


@method
@async_serialize
async def eth_uninstallFilter(filter_id):
    return thor.uninstall_filter(filter_id)


@method
@async_serialize
async def eth_getFilterChanges(filter_id):
    return await thor.get_filter_changes(filter_id)


@method
@async_serialize
async def eth_getLogs(filter_obj):
    return await thor.get_logs(filter_obj.get("address", None), input_log_filter_formatter(filter_obj))
