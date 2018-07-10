import rlp
from bitcoin import encode_privkey
from secp256k1 import PrivateKey
from hashlib import blake2b
from .types import (
    strip_0x,
    encode_number,
    decode_hex,
    bytearray_to_bytestr,
)
from rlp.sedes import (
    big_endian_int,
    CountableList,
    binary,
)


def noop(value):
    return value


#
# block
#
ETH_BLOCK_KWARGS_MAP = {
    "id": "hash",
    "parentID": "parentHash",
    "signer": "miner",
    "totalScore": "totalDifficulty",
    "txsRoot": "transactionsRoot",
}


BLOCK_FORMATTERS = {
    "number": encode_number,
    "size": encode_number,
    "timestamp": encode_number,
    "gasLimit": encode_number,
    "gasUsed": encode_number,
    "totalScore": encode_number,
}


def thor_block_convert_to_eth_block(block):
    return {
        ETH_BLOCK_KWARGS_MAP.get(k, k): BLOCK_FORMATTERS.get(k, noop)(v)
        for k, v in block.items()
    }


#
# receipt
#
def thor_receipt_convert_to_eth_receipt(receipt):
    return {
        "status": encode_number(0 if receipt["reverted"] else 1),
        "transactionHash": receipt["meta"]["txID"],
        "transactionIndex": encode_number(0),
        "blockNumber": encode_number(receipt["meta"]["blockNumber"]),
        "blockHash": receipt["meta"]["blockID"],
        "cumulativeGasUsed": encode_number(receipt["gasUsed"]),
        "gasUsed": encode_number(receipt["gasUsed"]),
        "contractAddress": None if receipt["reverted"] else receipt["outputs"][0]["contractAddress"],
        "logs": None if receipt["reverted"] else [
            thor_receipt_log_convert_to_eth_log(receipt, index, log)
            for index, log in enumerate(receipt["outputs"][0]["events"])
        ],
    }


#
# log
#
def thor_receipt_log_convert_to_eth_log(receipt, index, log):
    return {
        "type": "mined",
        "logIndex": encode_number(index),
        "transactionIndex": encode_number(0),
        "transactionHash": receipt["meta"]["txID"],
        "blockHash": receipt["meta"]["blockID"],
        "blockNumber": encode_number(receipt["meta"]["blockNumber"]),
        "address": log["address"],
        "data": log["data"],
        "topics": log["topics"],
    }


def thor_log_convert_to_eth_log(address, logs):
    if logs:
        return [
            {
                "logIndex": encode_number(index),
                "blockNumber": encode_number(log["meta"]["blockNumber"]),
                "blockHash": log["meta"]["blockID"],
                "transactionHash": log["meta"]["txID"],
                "transactionIndex": encode_number(0),
                "address": address,
                "data": log["data"],
                "topics": log["topics"],
            }
            for index, log in enumerate(logs)
        ]
    return []


#
# transaction
#
def thor_tx_convert_to_eth_tx(tx):
    return {
        "hash": tx["id"],
        "nonce": tx["nonce"],
        "blockHash": tx["meta"]["blockID"],
        "blockNumber": encode_number(tx["meta"]["blockNumber"]),
        "transactionIndex": encode_number(0),
        "from": tx["origin"],
        "to": tx["clauses"][0]["to"],
        "value": tx["clauses"][0]["value"],
        "gas": encode_number(tx["gas"]),
        "gasPrice": encode_number(1),
        "input": tx["clauses"][0]["data"]
    }


class Clause(rlp.Serializable):
    fields = [
        ("To", binary),
        ("Value", big_endian_int),
        ("Data", binary),
    ]

    def __init__(self, To, Value, Data):
        super(Clause, self).__init__(To, Value, Data)


class ThorTransaction(rlp.Serializable):
    fields = [
        ("ChainTag", big_endian_int),
        ("BlockRef", big_endian_int),
        ("Expiration", big_endian_int),
        ("Clauses", CountableList(Clause)),  # []
        ("GasPriceCoef", big_endian_int),
        ("Gas", big_endian_int),
        ("DependsOn", binary),  # b""
        ("Nonce", big_endian_int),
        ("Reserved", CountableList(object)),  # []
        ("Signature", binary),  # b""
    ]

    def __init__(self, thor, eth_tx):
        chain_tag = int(thor.get_block(0)["hash"][-2:], 16)
        blk_ref = int(strip_0x(thor.get_block("best")["hash"])[:8], 16)
        receiver = b"" if "to" not in eth_tx else decode_hex(eth_tx["to"])
        clauses = [
            Clause(
                receiver,
                eth_tx.get("value", 0),
                decode_hex(eth_tx.get("data", "")),
            )
        ]
        super(ThorTransaction, self).__init__(chain_tag, blk_ref, (2 ** 32) - 1, clauses, 0, eth_tx.get("gas", 3000000), b"", 0, [], b"")

    def sign(self, key):
        '''Sign this transaction with a private key.

        A potentially already existing signature would be overridden.
        '''
        if key in (0, "", b"\x00" * 32, "0" * 64):
            raise Exception("Zero privkey cannot sign")

        h = blake2b(digest_size=32)
        h.update(rlp.encode(self, ThorTransaction.exclude(["Signature"])))
        rawhash = h.digest()

        if len(key) == 64:
            # we need a binary key
            key = encode_privkey(key, "bin")

        pk = PrivateKey(key, raw=True)
        signature = pk.ecdsa_recoverable_serialize(
            pk.ecdsa_sign_recoverable(rawhash, raw=True)
        )
        self.Signature = signature[0] + bytearray_to_bytestr([signature[1]])


#
# estimate eth gas
#
TX_GAS = 5000
CLAUSE_GAS = 21000 - TX_GAS
CLAUSE_GAS_CONTRACT_CREATION = 53000 - TX_GAS
TX_DATA_ZERO_GAS = 4
TX_DATA_NON_ZERO_GAS = 68


def data_gas(data):
    data = decode_hex(data)
    if len(data) == 0:
        return 0
    z = 0
    nz = 0
    for byt in data:
        if byt == 0:
            z += 1
        else:
            nz += 1
    return (TX_DATA_ZERO_GAS * z) + (TX_DATA_NON_ZERO_GAS * nz)


def intrinsic_gas(transaction):
    total = TX_GAS
    gas = data_gas(transaction["data"])
    total += gas
    cgas = CLAUSE_GAS
    if "to" not in transaction:
        cgas = CLAUSE_GAS_CONTRACT_CREATION
    total += cgas
    return total
