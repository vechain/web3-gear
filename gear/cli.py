import click
import requests
from .thor.client import thor
from .thor.account import (
    solo,
    keystore as _keystore,
)
from .rpc import web3_clientVersion
from aiohttp import web
from jsonrpcserver import async_dispatch


res_headers = {
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept",
    "Access-Control-Allow-Origin": "*",
    "Connection": "keep-alive",
}


async def handle(request):
    request = await request.text()
    response = await async_dispatch(request, basic_logging=True)
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
def run_server(host, port, endpoint, keystore, passcode):
    try:
        response = requests.options(endpoint)
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

    app = web.Application()
    app.router.add_post("/", handle)
    app.router.add_options("/", lambda r: web.Response(headers=res_headers))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    run_server()
