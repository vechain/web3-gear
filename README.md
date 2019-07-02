# Web3-gear &nbsp;&nbsp; [![Gitter](https://badges.gitter.im/vechain/thor.svg)](https://gitter.im/vechain/thor?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

Proxy [Thor](https://github.com/vechain/thor)'s RESTful API to Eth JSON-RPC, to support Remix, Truffle and more (You should give priority to using Thor's RESTful API).

Working with [Thor Builtins](https://github.com/vechain/thor-builtins) will make Web3-Gear more usable.

# Quick Start

## Installation

### On OS X

* Python 3.6+ support

1. Install the system-dependecies

    ```
    brew install openssl
    export CFLAGS="-I$(brew --prefix openssl)/include $CFLAGS"
    export LDFLAGS="-L$(brew --prefix openssl)/lib $LDFLAGS"
    ```

2. Installation of Web3-Gear and it's dependent Python packages via PyPI

    ```
    pip3 install web3-gear
    ```

### On Ubuntu

* Python 3.6+ support

1. Install the system-dependecies

    ```
    sudo apt-get install build-essential libssl-dev python-dev
    ```

2. Use a virtual environment to isolate your web3-gear project

    ```
    python3 -m venv thor-venv
    source thor-venv/bin/activate
    ```

3. Installation of Web3-Gear and it's dependent Python packages via PyPI

    ```
    pip3 install web3-gear
    ```

Note that you can activate and deactivate your virtual environment now

```
source thor-venv/bin/activate
deactivate
```

See https://docs.python.org/3/library/venv.html for more information

### On Windows

* Python 3.6 support

1. Install Visual C++ Build Tools.

2. Install [scrypt-py](https://pypi.org/project/scrypt/#files) use the precompiled wheels.

3. Installation of Web3-Gear and it's dependent Python packages via PyPI

    ```
    pip3 install web3-gear
    ```

## Run

Installing through pip will make the ``web3-gear`` command available on your machine (`must run thor client first.`)

```
web3-gear
```

This will run web3-gear on `127.0.0.1:8545`.

You can change its default behavior with the following parameters:

- **host**: rpc service host, eg: `--host 127.0.0.1`
- **port**: rpc service port, eg: `--port 8545`
- **endpoint**: thor restful service endpoint, eg: `--endpoint http://127.0.0.1:8669`
- **keystore**: keystore file path, eg: `--keystore /Users/(username)/keystore)`, default=thor stand-alone(solo) built-in accounts
- **passcode**: passcode of keystore, eg: `--passcode xxxxxxxx`
- **debug**: bool default=false, whether to display debug logs, eg: `--debug true`
- **log**: bool default=false, whether to display rpc logs, eg: `--log false`

### Use Remix

Change the Remix environment to Web3 provide.

![](http://oi64.tinypic.com/2u59gef.jpg)

### Use Truffle

* Truffle 4.0.6+ support

Modify the configuration of truffle first(`truffle.js`):

```js
module.exports = {
    networks: {
        development: {
            host: "localhost",
            port: 8545,
            network_id: "*" // Match any network id
        }
    }
};
```

Then you can use truffle's command line tool.

There are some projects based on truffle, can use them for testing:

- [Crowdsale Contracts](https://github.com/vechain/crowdsale-contracts).
- [Token Distribution](https://github.com/libotony/token-distribution).
- [Solidity Idiosyncrasies](https://github.com/miguelmota/solidity-idiosyncrasies).
