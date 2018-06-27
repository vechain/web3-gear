import json
from gear.utils.keystore import (
    decode_keystore_json,
    priv_to_addr,
)


class account(object):
    def __init__(self):
        self.accounts = {}

    def get_accounts(self):
        return list(self.accounts.keys())

    def get_priv_by_addr(self, adrr):
        return self.accounts[adrr]


class solo(account):
    def __init__(self):
        priv_keys = [
            "dce1443bd2ef0c2631adc1c67e5c93f13dc23a41c18b536effbbdcbcdb96fb65",
            "321d6443bc6177273b5abf54210fe806d451d6b7973bccc2384ef78bbcd0bf51",
            "2d7c882bad2a01105e36dda3646693bc1aaaa45b0ed63fb0ce23c060294f3af2",
            "593537225b037191d322c3b1df585fb1e5100811b71a6f7fc7e29cca1333483e",
            "ca7b25fc980c759df5f3ce17a3d881d6e19a38e651fc4315fc08917edab41058",
            "88d2d80b12b92feaa0da6d62309463d20408157723f2d7e799b6a74ead9a673b",
            "fbb9e7ba5fe9969a71c6599052237b91adeb1e5fc0c96727b66e56ff5d02f9d0",
            "547fb081e73dc2e22b4aae5c60e2970b008ac4fc3073aebc27d41ace9c4f53e9",
            "c8c53657e41a8d669349fc287f57457bd746cb1fcfc38cf94d235deb2cfca81b",
            "87e0eba9c86c494d98353800571089f316740b0cb84c9a7cdf2fe5c9997c7966",
        ]
        self.accounts = {
            priv_to_addr(priv_key): priv_key
            for priv_key in priv_keys
        }


class keystore(account):
    def __init__(self, keystore_path, passcode):
        jsondata = json.loads(open(keystore_path).read())
        priv_key = decode_keystore_json(jsondata, passcode)
        self.accounts = {
            priv_to_addr(priv_key): priv_key,
        }
