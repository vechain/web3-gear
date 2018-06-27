Give thor a RPC-API like Ehereum, now it's mainly to be able to use Remix on `Thor <https://github.com/vechain/thor>`_.

Working with `builtin-contracts <https://github.com/z351522453/builtin-contracts>`_ will make Web3-Gear more usable.

Installation on OS X
--------------------

First install the system-dependecies for a successful build of secp256k1-py:

::

    brew install automake libtool pkg-config libffi gmp openssl

Installation of Web3-Gear and it's dependent Python packages via PyPI:

::

    pip3 install web3-gear

Run
---
Installing through pip will make the ``web3-gear`` command available on your machine:

::

    web3-gear

This will run web3-gear on 127.0.0.1:8545.

You can change its default behavior with the following parameters:

- host, rpc service host, default=127.0.0.1
- port, rpc service port default=8545
- endpoint, thor restful service endpoint, default=http://127.0.0.1:8669
- keystore, keystore file path (eg: /Users/(username)/keystore), default=thor stand-alone(solo) built-in accounts
- passcode, passcode of keystore
