import os
import pbkdf2
import scrypt
from eth_keys import keys
from eth_utils import to_bytes
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Hash import (
    SHA256,
    keccak,
)
from gear.utils.types import (
    encode_hex,
    decode_hex,
    big_endian_to_int
)


PBKDF2_CONSTANTS = {
    "prf": "hmac-sha256",
    "dklen": 32,
    "c": 262144
}


def mk_pbkdf2_params():
    params = PBKDF2_CONSTANTS.copy()
    params['salt'] = encode_hex(os.urandom(16))
    return params


def pbkdf2_hash(val, params):
    assert params["prf"] == "hmac-sha256"
    return pbkdf2.PBKDF2(val, decode_hex(params["salt"]), params["c"],
                         SHA256).read(params["dklen"])


SCRYPT_CONSTANTS = {
    "n": 262144,
    "r": 1,
    "p": 8,
    "dklen": 32
}


def mk_scrypt_params():
    params = SCRYPT_CONSTANTS.copy()
    params['salt'] = encode_hex(os.urandom(16))
    return params


def scrypt_hash(val, params):
    return scrypt.hash(str(val), decode_hex(params["salt"]), params["n"],
                       params["r"], params["p"], params["dklen"])


kdfs = {
    "pbkdf2": {
        "calc": pbkdf2_hash,
        "mkparams": mk_pbkdf2_params
    },
    "scrypt": {
        "calc": scrypt_hash,
        "mkparams": mk_scrypt_params
    }
}


def aes_ctr_encrypt(text, key, params):
    iv = big_endian_to_int(decode_hex(params["iv"]))
    ctr = Counter.new(128, initial_value=iv, allow_wraparound=True)
    mode = AES.MODE_CTR
    encryptor = AES.new(key, mode, counter=ctr)
    return encryptor.encrypt(text)


def aes_ctr_decrypt(text, key, params):
    iv = big_endian_to_int(decode_hex(params["iv"]))
    ctr = Counter.new(128, initial_value=iv, allow_wraparound=True)
    mode = AES.MODE_CTR
    encryptor = AES.new(key, mode, counter=ctr)
    return encryptor.decrypt(text)


def aes_mkparams():
    return {"iv": encode_hex(os.urandom(16))}


ciphers = {
    "aes-128-ctr": {
        "encrypt": aes_ctr_encrypt,
        "decrypt": aes_ctr_decrypt,
        "mkparams": aes_mkparams
    }
}


def sha3_256(x):
    return keccak.new(digest_bits=256, data=x)


def sha3(seed):
    return sha3_256(seed).digest()


def priv_to_addr(x):
    if len(x) == 64:
        key = to_bytes(hexstr=x)  # we need a binary key
    return keys.PrivateKey(key).public_key.to_address()


def decode_keystore_json(jsondata, pw):
    # Get KDF function and parameters
    if "crypto" in jsondata:
        cryptdata = jsondata["crypto"]
    elif "Crypto" in jsondata:
        cryptdata = jsondata["Crypto"]
    else:
        raise Exception("JSON data must contain \"crypto\" object")
    kdfparams = cryptdata["kdfparams"]
    kdf = cryptdata["kdf"]
    if cryptdata["kdf"] not in kdfs:
        raise Exception("Hash algo %s not supported" % kdf)
    kdfeval = kdfs[kdf]["calc"]
    # Get cipher and parameters
    cipherparams = cryptdata["cipherparams"]
    cipher = cryptdata["cipher"]
    if cryptdata["cipher"] not in ciphers:
        raise Exception("Encryption algo %s not supported" % cipher)
    decrypt = ciphers[cipher]["decrypt"]
    # Compute the derived key
    derivedkey = kdfeval(pw, kdfparams)
    assert len(derivedkey) >= 32, \
        "Derived key must be at least 32 bytes long"
    # print(b'derivedkey: ' + encode_hex(derivedkey))
    enckey = derivedkey[:16]
    # print(b'enckey: ' + encode_hex(enckey))
    ctext = decode_hex(cryptdata["ciphertext"])
    # Decrypt the ciphertext
    o = decrypt(ctext, enckey, cipherparams)
    # Compare the provided MAC with a locally computed MAC
    # print(b'macdata: ' + encode_hex(derivedkey[16:32] + ctext))
    mac1 = sha3(derivedkey[16:32] + ctext)
    mac2 = decode_hex(cryptdata["mac"])
    if mac1 != mac2:
        raise ValueError("MAC mismatch. Passcode incorrect?")
    return encode_hex(o)
