import json
import uuid
from datetime import datetime
import asyncio
import subprocess

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
        self.known_commands = dict()
        self.register_command('version',
                              'version string for rcomp server',
                              self.version)
        self.register_command('date',
                              ('get current time on the server,'
                               ' mostly of interest for testing.'),
                              self.date)
        self.register_command('status ID',
                              ('get status of and, if available, results'
                               ' from job identified by ID'),
                              self.status,
                              route='/status/{ID}',
                              hidden=True)
        self.register_command('trivial',
                              ('command that immediately completes with'
                               ' success, mostly of interest for testing.'),
                              self.trivial,
                              ['get', 'post'])

    def register_command(self, name, summary, function, methods=None, route=None, hidden=False):
        """register new command in rcomp server.

        if `route` is not given, then `name` is used to form the route
        corresponding to this command. As such, it must be URL-safe.

        if `methods` is not given, then assume only HTTP method
        support is GET.
        """
        assert name not in self.known_commands
        if methods is None:
            methods = ['get']
        if route is None:
            route = '/' + name
        if not hidden:
            self.known_commands[name] = {'name': name,
                                         'summary': summary,
                                         'http_methods': methods,
                                         'route': route}
        for method in methods:
            self.app.router.add_route(method, route, function)

    async def start_redis(self, app):
        app['redis'] = redis.StrictRedis()

    async def index(self, request):
        return web.json_response({'commands': self.known_commands})

    async def version(self, request):
        return web.json_response({'version': __version__})

    async def generic_task(self, job_id, cmd):
        pr = await asyncio.create_subprocess_exec(*(cmd.split()), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = await pr.communicate()
        self.app['redis'].hset(job_id, 'output', stdout_data)
        self.app['redis'].hset(job_id, 'done', 1)

    async def call_generic(self, cmd):
        job_id = str(uuid.uuid4())
        start_time = str(datetime.utcnow())
        self.app['redis'].hset(job_id, 'cmd', cmd)
        self.app['redis'].hset(job_id, 'stime', start_time)
        self.app['redis'].hset(job_id, 'done', 0)
        self.app.loop.create_task(self.generic_task(job_id, cmd))
        return job_id

    async def date(self, request):
        job_id = await self.call_generic('date')
        return await self.get_status(job_id)

    async def get_status(self, job_id):
        if not self.app['redis'].exists(job_id):
            return web.Response(status=404,
                                text=json.dumps({'err': 'job not found'}))
        cmd = str(self.app['redis'].hget(job_id, 'cmd'),
                  encoding='utf-8')
        start_time = str(self.app['redis'].hget(job_id, 'stime'),
                         encoding='utf-8')
        done = (False
                if int(self.app['redis'].hget(job_id, 'done')) == 0
                else True)
        resp = {
            'cmd': cmd,
            'id': job_id,
            'stime': start_time,
            'done': done
        }
        if done:
            resp['output'] = str(self.app['redis'].hget(job_id, 'output'),
                                 encoding='utf-8')
        return web.json_response(resp)

    async def status(self, request):
        job_id = request.match_info['ID']
        return await self.get_status(job_id)

    async def trivial(self, request):
        job_id = str(uuid.uuid4())
        start_time = str(datetime.utcnow())
        request.app['redis'].hset(job_id, 'cmd', 'trivial')
        request.app['redis'].hset(job_id, 'stime', start_time)
        request.app['redis'].hset(job_id, 'done', 1)
        request.app['redis'].hset(job_id, 'output', '')
        return await self.get_status(job_id)

    def run(self):
        web.run_app(self.app, host=self._host, port=self._port)
