from aiohttp import web

from . import __version__


class Server:
    def __init__(self, host='127.0.0.1', port=8080):
        self._host = host
        self._port = port
        self.app = web.Application()
        self.app.router.add_get('/', self.index)
        self.known_commands = ['version']
        self.app.router.add_get('/version', self.version)

    def index(self, request):
        return web.json_response({'commands': self.known_commands})

    def version(self, request):
        return web.json_response({'version': __version__})

    def run(self):
        web.run_app(self.app, host=self._host, port=self._port)
