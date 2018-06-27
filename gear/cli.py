import time
import click
import random
import requests
from .thor.client import thor
from .thor.account import (
    solo,
    keystore as _keystore,
)
from .utils.thread import spawn
from .rpc import (
    application,
    web3_clientVersion,
)
from wsgiref.simple_server import (
    make_server,
    WSGIRequestHandler,
)


class SilentWSGIRequestHandler(WSGIRequestHandler):
    """
    WSGIRequestHandler 会输出所有的 request info, 重写 log_request 以保持输出干净.
    """

    def log_request(self, code="-", size="-"):
        return


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
)
@click.option(
    "--port",
    default=8545,
    type=int,
)
@click.option(
    "--endpoint",
    default="http://127.0.0.1:8669",
)
@click.option(
    "--keystore",
    default="",
)
@click.option(
    "--passcode",
    default="",
)
def run_server(host, port, endpoint, keystore, passcode):
    try:
        response = requests.options("http://127.0.0.1:8669/")
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Unable to connect to Thor-Restful server.")
        return

    print(web3_clientVersion())
    print("Listening on %s:%s" % (host, port))

    thor.set_endpoint(endpoint)
    if keystore == "":
        thor.set_accounts(solo())
    else:
        thor.set_accounts(_keystore(keystore, passcode))

    server = make_server(
        host,
        port,
        application,
        handler_class=SilentWSGIRequestHandler
    )
    spawn(server.serve_forever)

    try:
        while True:
            time.sleep(random.random())
    except KeyboardInterrupt:
        try:
            server.stop()
        except AttributeError:
            server.shutdown()


if __name__ == '__main__':
    run_server()
