import uuid
from datetime import datetime

from aiohttp import web
import redis

from . import __version__


class Server:
    def __init__(self, host='127.0.0.1', port=8080):
        self._host = host
        self._port = port
        self.app = web.Application()
        self.app.on_startup.append(self.start_redis)
        self.app.router.add_get('/', self.index)
        self.known_commands = [
            {'name': 'version',
             'summary': 'version string for rcomp server',
             'http_methods': ['get']},
            {'name': 'trivial',
             'summary': ('command that immediately completes with success,'
                         ' mostly of interest for testing.'),
             'http_methods': ['get', 'post']}
        ]
        self.app.router.add_get('/version', self.version)
        self.app.router.add_post('/trivial', self.trivial)

    async def start_redis(self, app):
        app['redis'] = redis.StrictRedis()

    async def index(self, request):
        return web.json_response({'commands': self.known_commands})

    async def version(self, request):
        return web.json_response({'version': __version__})

    async def trivial(self, request):
        job_id = str(uuid.uuid4())
        start_time = str(datetime.utcnow())
        request.app['redis'].hset(job_id, 'cmd', 'trivial')
        request.app['redis'].hset(job_id, 'stime', start_time)
        request.app['redis'].hset(job_id, 'done', 1)
        request.app['redis'].hset(job_id, 'output', '')
        return web.json_response({
            'cmd': str(request.app['redis'].hget(job_id, 'cmd'),
                       encoding='utf-8'),
            'id': job_id,
            'stime': str(request.app['redis'].hget(job_id, 'stime'),
                         encoding='utf-8'),
            'done': (False
                     if request.app['redis'].hget(job_id, 'done') == 0
                     else True),
            'output': str(request.app['redis'].hget(job_id, 'output'),
                          encoding='utf-8')
        })

    def run(self):
        web.run_app(self.app, host=self._host, port=self._port)
