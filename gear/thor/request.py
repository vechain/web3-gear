import aiohttp


async def post(endpoint_uri, data, **kwargs):
    async with aiohttp.ClientSession() as session:
        return await session.post(endpoint_uri, json=data, **kwargs)


async def get(endpoint_uri, params, **kwargs):
    async with aiohttp.ClientSession() as session:
        return await session.get(endpoint_uri, params=params, **kwargs)


class Restful(object):

    def __init__(self, endpoint):
        super(Restful, self).__init__()
        self._endpoint = endpoint

    def __call__(self, parameter):
        if parameter is not None:
            return Restful('%s/%s' % (self._endpoint, parameter))
        return self

    def __getattr__(self, resource):
        return Restful('%s/%s' % (self._endpoint, resource))

    async def make_request(self, method, params=None, data=None, **kwargs):
        headers = {
            "accept": "application/json",
            "Connection": "keep-alive",
            "Content-Type": "application/json"
        }
        kwargs.setdefault('headers', headers)
        kwargs.setdefault('timeout', 10)
        try:
            response = await method(self._endpoint, params=params, data=data, **kwargs)
            response.raise_for_status()
            return await response.json()
        except aiohttp.ClientConnectionError as e:
            print("Unable to connect to Thor-Restful server:")
            print(e)
        except Exception as e:
            print("Thor-Restful server Err:")
            print(e)
            print(response.text())
            raise ValueError(response.text().strip('\n'))
        return None
