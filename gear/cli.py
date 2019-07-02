import click
import requests
from .thor.client import thor
from .thor.account import (
    solo,
    keystore as _keystore,
)
from .rpc import make_version
from aiohttp import web
from jsonrpcserver import async_dispatch


res_headers = {
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept",
    "Access-Control-Allow-Origin": "*",
    "Connection": "keep-alive",
}


async def handle(request, logging=False, debug=False):
    request = await request.text()
    response = await async_dispatch(request, basic_logging=logging, debug=debug)
    if response.wanted:
        return web.json_response(response.deserialized(), headers=res_headers, status=response.http_status)
    else:
        return web.Response(headers=res_headers, content_type="text/plain")


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
@click.option(
    "--log",
    default=False,
    type=bool,
)
@click.option(
    "--debug",
    default=False,
    type=bool,
)
def run_server(host, port, endpoint, keystore, passcode, log, debug):
    try:
        response = requests.options(endpoint)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Unable to connect to Thor-Restful server.")
        return

    print(make_version())
    print("Listening on %s:%s" % (host, port))

    thor.set_endpoint(endpoint)
    if keystore == "":
        thor.set_accounts(solo())
    else:
        thor.set_accounts(_keystore(keystore, passcode))

    app = web.Application()
    app.router.add_post("/", lambda r: handle(r, log, debug))
    app.router.add_options("/", lambda r: web.Response(headers=res_headers))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    run_server()
