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
            "99f0500549792796c14fed62011a51081dc5b5e68fe8bd8a13b86be829c4fd36",
            "7b067f53d350f1cf20ec13df416b7b73e88a1dc7331bc904b92108b1e76a08b1",
            "f4a1a17039216f535d42ec23732c79943ffb45a089fbb78a14daad0dae93e991",
            "35b5cc144faca7d7f220fca7ad3420090861d5231d80eb23e1013426847371c4",
            "10c851d8d6c6ed9e6f625742063f292f4cf57c2dbeea8099fa3aca53ef90aef1",
            "2dd2c5b5d65913214783a6bd5679d8c6ef29ca9f2e2eae98b4add061d0b85ea0",
            "e1b72a1761ae189c10ec3783dd124b902ffd8c6b93cd9ff443d5490ce70047ff",
            "35cbc5ac0c3a2de0eb4f230ced958fd6a6c19ed36b5d2b1803a9f11978f96072",
            "b639c258292096306d2f60bc1a8da9bc434ad37f15cd44ee9a2526685f592220",
            "9d68178cdc934178cca0a0051f40ed46be153cf23cb1805b59cc612c0ad2bbe0",
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
