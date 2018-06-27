import codecs
import functools
from eth_utils import is_hex
from rlp.utils import (
    big_endian_to_int,
    int_to_big_endian,
    encode_hex,
    decode_hex as _decode_hex,
)


def bytearray_to_bytestr(value):
    return bytes(value)


def is_numeric(value):
    return isinstance(value, int)


def is_binary(value):
    return isinstance(value, (bytes, bytearray))


def is_text(value):
    return isinstance(value, str)


def is_string(value):
    return isinstance(value, (bytes, str, bytearray))


def is_integer(value):
    return isinstance(value, int)


def is_array(value):
    return isinstance(value, (list, tuple))


def force_text(value):
    if is_text(value):
        return value
    elif is_binary(value):
        return codecs.decode(value, "iso-8859-1")
    else:
        raise TypeError("Unsupported type: {0}".format(type(value)))


def force_bytes(value):
    if is_binary(value):
        return bytes(value)
    elif is_text(value):
        return codecs.encode(value, "iso-8859-1")
    else:
        raise TypeError("Unsupported type: {0}".format(type(value)))


def force_obj_to_text(obj, skip_unsupported=False):
    if is_string(obj):
        return force_text(obj)
    elif isinstance(obj, dict):
        return {
            k: force_obj_to_text(v, skip_unsupported) for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return type(obj)(force_obj_to_text(v, skip_unsupported) for v in obj)
    elif not skip_unsupported:
        raise ValueError("Unsupported type: {0}".format(type(obj)))
    else:
        return obj


def force_obj_to_bytes(obj, skip_unsupported=False):
    if is_string(obj):
        return force_bytes(obj)
    elif isinstance(obj, dict):
        return {
            k: force_obj_to_bytes(v, skip_unsupported) for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return type(obj)(force_obj_to_bytes(v, skip_unsupported) for v in obj)
    elif not skip_unsupported:
        raise ValueError("Unsupported type: {0}".format(type(obj)))
    else:
        return obj


def coerce_args_to_bytes(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        bytes_args = force_obj_to_bytes(args, True)
        bytes_kwargs = force_obj_to_bytes(kwargs, True)
        return fn(*bytes_args, **bytes_kwargs)
    return inner


def coerce_return_to_bytes(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        return force_obj_to_bytes(fn(*args, **kwargs), True)
    return inner


@coerce_args_to_bytes
def strip_0x(value):
    if value.startswith(b'0x'):
        return value[2:]
    return value


@coerce_args_to_bytes
def add_0x(value):
    return b"0x" + strip_0x(value)


@coerce_return_to_bytes
def encode_data(data, length=None):
    '''Encode unformatted binary `data`.

    If `length` is given, the result will be padded like this: ``quantity_encoder(255, 3) ==
    '0x0000ff'``.
    '''

    def zpad(x, l):
        ''' Left zero pad value `x` at least to length `l`.

        >>> zpad('', 1)
        '\x00'
        >>> zpad('\xca\xfe', 4)
        '\x00\x00\xca\xfe'
        >>> zpad('\xff', 1)
        '\xff'
        >>> zpad('\xca\xfe', 2)
        '\xca\xfe'
        '''
        return b'\x00' * max(0, l - len(x)) + x
    return add_0x(encode_hex(zpad(data, length or 0)))


@coerce_return_to_bytes
def encode_number(value, length=None):
    '''Encode interger quantity `data`.'''
    if not is_numeric(value):
        raise ValueError("Unsupported type: {0}".format(type(value)))
    hex_value = encode_data(int_to_big_endian(value), length)

    if length:
        return hex_value
    else:
        return add_0x(strip_0x(hex_value).lstrip(b'0') or b'0')


@coerce_args_to_bytes
def decode_hex(value):
    return _decode_hex(strip_0x(value))


@coerce_args_to_bytes
def normalize_number(value):
    if is_numeric(value):
        return value
    elif is_string(value):
        if value.startswith(b'0x'):
            return int(value, 16)
        else:
            return big_endian_to_int(value)
    else:
        raise ValueError("Unknown numeric encoding: {0}".format(value))


def normalize_block_identifier(block_identifier):
    if is_hex(block_identifier):
        return block_identifier
    if block_identifier is None or block_identifier == "earliest":
        return normalize_number(0)
    if block_identifier in ["best", "latest", "pending"]:  # eth 最新块用 latest 表示
        return "best"
    return normalize_number(block_identifier)
