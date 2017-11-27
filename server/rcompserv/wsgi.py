"""Facilitate use of WSGI servers with rcomp

e.g., Gunicorn <http://gunicorn.org/>, which can be used by

    gunicorn -b '127.0.0.1:8000' -w 9 -k aiohttp.GunicornWebWorker rcompserv.wsgi:main

Requests can be sent to <http://127.0.0.1:8000>, e.g.,

    curl http://127.0.0.1:8000/
"""
from .serv import Server
main = Server().app
