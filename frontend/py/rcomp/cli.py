"""command-line interface (CLI)

For local development, use the `-s` switch to direct this client at
the localhost. E.g.,

    rcomp -s http://127.0.0.1:8000
"""
import argparse
import sys
import time
import json
import os.path
import os
import base64
import zlib

import requests

from . import __version__


def get(uri, verbose=False):
    if verbose:
        print('> GET {}'.format(uri))
    res = requests.get(uri)
    if verbose:
        print_httpresponse(res)
    return res

def post(uri, payload=None, verbose=False):
    """Wrapper for requests.post()

    If given, payload should be a `dict` object. Internally it is
    translated to JSON before calling requests.post().
    """
    if verbose:
        print('> POST {}'.format(uri))
        if payload is not None:
            print('> {}'.format(payload))
    if payload is None:
        res = requests.post(uri)
    else:
        res = requests.post(uri, json=payload)
    if verbose:
        print_httpresponse(res)
    return res

def print_httpresponse(res, prefix='< '):
    print('{PREFIX}{STATUS_CODE} {REASON}'.format(PREFIX=prefix, STATUS_CODE=res.status_code, REASON=res.reason))
    for hname, value in res.headers.items():
        print('{PREFIX}{HNAME}: {VALUE}'.format(PREFIX=prefix, HNAME=hname, VALUE=value))
    if len(res.text) > 0:
        print('{PREFIX}{TEXT}'.format(PREFIX=prefix, TEXT=res.text))


def find_files(command, argv):
    """Find files for given command.

    return copy of argv where file names are replaced with
    zlib-compressed file data.
    """
    if command == 'ltl2ba':
        start = 0
        while True:
            try:
                start = argv.index('-F', start) + 1
            except ValueError:
                break
            with open(argv[start], 'rb') as fp:
                argv[start] = str(base64.b64encode(zlib.compress(fp.read())),
                                  encoding='utf-8')
        return argv
    elif command == 'gr1c':
        all_files = False
        for ii in range(len(argv)):
            if argv[ii] == '--':
                all_files = True
            elif all_files or argv[ii][0] != '-':
                with open(argv[ii], 'rb') as fp:
                    argv[ii] = str(base64.b64encode(zlib.compress(fp.read())),
                                   encoding='utf-8')
        return argv
    else:
        # Do nothing for unrecognized commands and those that do not
        # require treatment of file data.
        return argv


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rcomp', add_help=False)
    parser.add_argument('-h', '--help', action='store_true',
                        dest='show_help',
                        help='print this help message and exit')
    parser.add_argument('-V', '--version', action='store_true',
                        dest='show_version',
                        help='print version number and exit')
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', default=False,
                        help=('be verbose; print JSON data from outgoing'
                              ' and incoming messages'))
    parser.add_argument('-s', '--server', metavar='URI',
                        dest='base_uri',
                        help=('base URI for job requests.'
                              ' (default is https://api.fmtools.org)'))
    parser.add_argument('--no-block', action='store_true',
                        dest='nonblocking', default=False,
                        help=('Default behavior is to wait for remote job'
                              ' to complete. Use this switch to immediately'
                              ' return after job successfully starts.'))
    parser.add_argument('--continue', metavar='JOBID',
                        dest='job_id', default=False, nargs='?',
                        help='')
    parser.add_argument('-t', '--timeout', metavar='T',
                        dest='timeout', type=int,
                        help=('maximum duration (seconds) of remote job;'
                              ' if 0, then no timeout restriction is used.'
                              ' default behavior is no timeout, but note'
                              ' that `rcomp` servers can still impose one.'))
    parser.add_argument('--cache-path', metavar='PATH',
                        dest='cachepath', default=None,
                        help=('path to cache file; default is .rcompcache'
                              ' in the directory from which `rcomp` client'
                              ' is called.'))
    parser.add_argument('--print-cache', action='store_true',
                        dest='print_cache', default=False,
                        help='print known jobs from the local rcomp cache.')
    parser.add_argument('COMMAND', nargs='?')
    parser.add_argument('ARGV', nargs=argparse.REMAINDER)

    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.show_help:
        parser.print_help()
        return 0

    if args.show_version:
        print('rcomp '+__version__)
        return 0

    if args.base_uri is None:
        base_uri = 'https://api.fmtools.org'
    else:
        base_uri = args.base_uri

    if args.cachepath is None:
        rcompcache_path = '.rcompcache'
    else:
        rcompcache_path = args.cachepath
    rcompcache_path = os.path.join(os.path.abspath(os.getcwd()), rcompcache_path)

    if args.print_cache:
        if os.path.exists(rcompcache_path):
            with open(rcompcache_path) as fp:
                rcompcache = json.load(fp)
        else:
            rcompcache = dict()
        if len(rcompcache) == 0:
            print('The local cache is empty.')
        else:
            for k, v in rcompcache.items():
                print('job: {}'.format(k))
                print('\tcommand: {}'.format(v['cmd']))
                print('\tstart time: {}'.format(v['stime']))
        return 0

    if (args.COMMAND is None) and (args.job_id is False):
        res = get(base_uri+'/', verbose=args.verbose)
        if res.ok:
            index = json.loads(res.text)
            assert 'commands' in index
            print('The following commands are available at {}'
                  .format(base_uri))
            for cmd in index['commands'].values():
                print('{NAME}\t\t{SUMMARY}'
                      .format(NAME=cmd['name'], SUMMARY=cmd['summary']))

    elif args.COMMAND == 'version':
        res = get(base_uri+'/' + args.COMMAND, verbose=args.verbose)
        if res.ok:
            print(res.text)

    else:
        if (args.job_id is not False) or args.nonblocking:
            if os.path.exists(rcompcache_path):
                with open(rcompcache_path) as fp:
                    rcompcache = json.load(fp)
            else:
                rcompcache = dict()
        if args.job_id is False:
            if args.ARGV is None:
                argv = []
            else:
                argv = args.ARGV
            payload = {'argv': find_files(args.COMMAND, argv)}
            if args.timeout is not None:
                payload['timeout'] = args.timeout
            res = post(base_uri+'/' + args.COMMAND, payload, verbose=args.verbose)
            if not res.ok:
                print('Error occurred while sending initial request to the server!')
                sys.exit(1)
            msg = json.loads(res.text)
            if not msg['done'] and args.nonblocking:
                assert msg['id'] not in rcompcache
                rcompcache[msg['id']] = {
                    'cmd': msg['cmd'],
                    'stime': msg['stime'],
                    'done': False
                }
                with open(rcompcache_path, 'w') as fp:
                    json.dump(rcompcache, fp)
                print('id: {}'.format(msg['id']))
                sys.exit(0)

        else:
            if args.job_id is None:
                earliest_job = None
                if len(rcompcache) == 0:
                    print('Error: `--continue` switch used but no jobs are known')
                    sys.exit(1)
                for k, v in rcompcache.items():
                    if (earliest_job is None) or (v['stime'] < rcompcache[earliest_job]['stime']):
                        earliest_job = k
                job_id = earliest_job
            else:
                job_id = args.job_id
            res = get(base_uri+'/status/' + job_id, verbose=args.verbose)
            if not res.ok:
                if res.status_code == 404:
                    print('Job {} is not known at {}'.format(job_id, base_uri))
                else:
                    print('Error occurred while communicating with server!')
                sys.exit(1)
            msg = json.loads(res.text)
            if msg['done']:
                rcompcache.pop(job_id)
                with open(rcompcache_path, 'w') as fp:
                    json.dump(rcompcache, fp)
                job_output = msg['output'].strip()
                if msg['ec'] != 0:
                    print('job_status: "{}"'.format(msg['status']))
                if len(job_output) > 0:
                    print(job_output)
                return msg['ec']  # use exitcode of remote job as that of this client
            else:
                print('id: {}'.format(msg['id']))
            sys.exit(0)

        while not msg['done']:
            time.sleep(0.1)
            res = get(base_uri+'/status/' + msg['id'], verbose=args.verbose)
            if not res.ok:
                print('Error occurred while communicating with server!')
                sys.exit(1)
            msg = json.loads(res.text)
        if msg['ec'] != 0:
            print('job_status: "{}"'.format(msg['status']))
        job_output = msg['output'].strip()
        if len(job_output) > 0:
            print(job_output)
        return msg['ec']  # use exitcode of remote job as that of this client

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
