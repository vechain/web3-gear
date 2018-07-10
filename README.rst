Web3-gear
---------

.. image:: https://badges.gitter.im/vechain/thor.svg
    :alt: Gitter
    :target: https://gitter.im/vechain/thor?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge

Give thor a RPC-API like Ethereum, now it's mainly to be able to use Remix & Truffle on `Thor <https://github.com/vechain/thor>`_.

Working with `builtin-contracts <https://github.com/z351522453/builtin-contracts>`_ will make Web3-Gear more usable.

Installation on OS X
--------------------

First install the system-dependecies for a successful build of secp256k1-py::

    brew install automake libtool pkg-config libffi gmp openssl

Installation of Web3-Gear and it's dependent Python packages via PyPI::

    pip3 install web3-gear

Run
---

Installing through pip will make the ``web3-gear`` command available on your machine (`must run thor client first.`)::

    web3-gear

This will run web3-gear on ``127.0.0.1:8545``.

You can change its default behavior with the following parameters:

--host      rpc service host, eg: ``--host 127.0.0.1``
--port      rpc service port, eg: ``--port 8545``
--endpoint  thor restful service endpoint, eg: ``--endpoint http://127.0.0.1:8669``
--keystore  keystore file path, eg: ``--keystore /Users/(username)/keystore)``, default=thor stand-alone(solo) built-in accounts
--passcode  passcode of keystore, eg: ``--passcode xxxxxxxx``

Use Remix
^^^^^^^^^

Change the Remix environment to Web3 provide.

.. image:: http://oi64.tinypic.com/5tw5kg.jpg

Use Truffle
^^^^^^^^^^^

Modify the configuration of truffle first(``truffle.js``):

.. code-block:: js

    module.exports = {
      networks: {
        development: {
          host: "localhost",
          port: 8545,
          network_id: "*" // Match any network id
        }
      }
    };

Then you can use truffle's command line tool.

There are some projects based on truffle, can use them for testing:

`Crowdsale Contracts <https://github.com/vechain/crowdsale-contracts>`_.

`Token Distribution <https://github.com/libotony/token-distribution>`_.

`Solidity Idiosyncrasies <https://github.com/miguelmota/solidity-idiosyncrasies>`_.
