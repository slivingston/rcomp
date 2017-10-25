import json
import uuid
from datetime import datetime
import asyncio
import subprocess
import base64
import os
import os.path
import tempfile
import zlib

from aiohttp import web
import redis

from . import __version__


class Server:
    def __init__(self, host='127.0.0.1', port=8080):
        self._host = host
        self._port = port
        self.extra_headers = {'Access-Control-Allow-Origin': '*'}
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
                              self.date,
                              ['get', 'post'])
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
        self.register_command('ltl2ba',
                              ('wrapper of LTL2BA (LTL2BA originally by'
                               ' Denis Oddoux and Paul Gastin)'),
                              self.ltl2ba,
                              ['get', 'post'])
        self.register_command('gr1c',
                              ('wrapper of gr1c (http://scottman.net/2012/gr1c)'),
                              self.gr1c,
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
        return web.json_response({'commands': self.known_commands},
                                 headers=self.extra_headers)

    async def version(self, request):
        return web.json_response({'version': __version__},
                                 headers=self.extra_headers)

    async def generic_task(self, job_id, cmd, temporary_dir=None):
        pr = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = await pr.communicate()
        self.app['redis'].hset(job_id, 'output', stdout_data)
        self.app['redis'].hset(job_id, 'done', 1)
        if (temporary_dir is not None) and len(temporary_dir) > 0:
            for fpath in os.listdir(temporary_dir):
                os.unlink(os.path.join(temporary_dir, fpath))
            os.rmdir(temporary_dir)

    async def call_generic(self, cmd, temporary_dir=None):
        job_id = str(uuid.uuid4())
        start_time = str(datetime.utcnow())
        self.app['redis'].hset(job_id, 'cmd', ' '.join(cmd))
        self.app['redis'].hset(job_id, 'stime', start_time)
        self.app['redis'].hset(job_id, 'done', 0)
        self.app.loop.create_task(self.generic_task(job_id, cmd, temporary_dir=temporary_dir))
        return job_id

    async def date(self, request):
        job_id = await self.call_generic(['date'])
        return await self.get_status(job_id)

    async def get_status(self, job_id):
        if not self.app['redis'].exists(job_id):
            return web.Response(status=404,
                                text=json.dumps({'err': 'job not found'}),
                                headers=self.extra_headers)
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
        return web.json_response(resp,
                                 headers=self.extra_headers)

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

    def map_files(self, command, argv):
        """Create temporary files from base64 encoded compressed data.

        If any temporary files are created, they will all be in the
        same temporary directory. If it is created, the path to this
        temporary directory is returned. Otherwise, an empty string is
        returned (instead of a path).

        return pair D and ARGV, where D is the path to temporary
        directory or empty string if no directory was created, and
        ARGV is copy of argv with compressed file data replaced by
        local paths to temporary files.

        The caller is responsible for deleting any temporary files or
        directories that are created.
        """
        if command == 'ltl2ba':
            start = 0
            temporary_dir = ''
            while True:
                try:
                    start = argv.index('-F', start) + 1
                except ValueError:
                    break
                if len(temporary_dir) == 0:
                    temporary_dir = tempfile.mkdtemp()
                fd, fname = tempfile.mkstemp(dir=temporary_dir)
                fp = os.fdopen(fd, 'wb')
                fp.write(zlib.decompress(base64.b64decode(bytes(argv[start], encoding='utf-8'),
                                                          validate=True)))
                fp.close()
                argv[start] = fname
            return temporary_dir, argv
        elif command == 'gr1c':
            temporary_dir = ''
            all_files = False
            for ii in range(len(argv)):
                if argv[ii] == '--':
                    all_files = True
                elif all_files or argv[ii][0] != '-':
                    if len(temporary_dir) == 0:
                        temporary_dir = tempfile.mkdtemp()
                    fd, fname = tempfile.mkstemp(dir=temporary_dir)
                    fp = os.fdopen(fd, 'wb')
                    fp.write(zlib.decompress(base64.b64decode(bytes(argv[ii], encoding='utf-8'),
                                                              validate=True)))
                    fp.close()
                    argv[ii] = fname
            return temporary_dir, argv
        else:
            return '', argv

    async def ltl2ba(self, request):
        if request.method == 'GET':
            return web.json_response({'err': 'not implemented'},
                                     headers=self.extra_headers)
        else:  # request.method == 'POST'
            argv = []
            if request.has_body:
                payload = json.loads(await request.read())
                if 'argv' in payload:
                    argv = payload['argv']
            temporary_dir, argv = self.map_files('ltl2ba', argv)
            job_id = await self.call_generic(['ltl2ba']+argv, temporary_dir)
            return await self.get_status(job_id)

    async def gr1c(self, request):
        if request.method == 'GET':
            return web.json_response({'err': 'not implemented'},
                                     headers=self.extra_headers)
        else:  # request.method == 'POST'
            argv = []
            if request.has_body:
                payload = json.loads(await request.read())
                if 'argv' in payload:
                    argv = payload['argv']
            temporary_dir, argv = self.map_files('gr1c', argv)
            job_id = await self.call_generic(['gr1c']+argv, temporary_dir)
            return await self.get_status(job_id)

    def run(self):
        web.run_app(self.app, host=self._host, port=self._port)
