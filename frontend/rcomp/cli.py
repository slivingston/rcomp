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

import requests

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rcomp', add_help=False)
    parser.add_argument('-h', '--help', action='store_true',
                        dest='show_help',
                        help='print this help message and exit')
    parser.add_argument('-V', '--version', action='store_true',
                        dest='show_version',
                        help='print version number and exit')
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
    parser.add_argument('--cache-path', metavar='PATH',
                        dest='cachepath', default=None)
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

    if (args.COMMAND is None) and (args.job_id is False):
        res = requests.get(base_uri+'/')
        if res.ok:
            index = json.loads(res.text)
            assert 'commands' in index
            print('The following commands are available at {}'
                  .format(base_uri))
            for cmd in index['commands'].values():
                print('{NAME}\t\t{SUMMARY}'
                      .format(NAME=cmd['name'], SUMMARY=cmd['summary']))

    elif args.COMMAND == 'version':
        res = requests.get(base_uri+'/' + args.COMMAND)
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
            res = requests.post(base_uri+'/' + args.COMMAND,
                                data=json.dumps({'argv': argv}))
            if not res.ok:
                print('Error occurred while sending initial request to the server!')
                sys.exit(1)
            msg = json.loads(res.text)
            if not msg['done'] and args.nonblocking:
                assert msg['id'] not in rcompcache
                rcompcache[msg['id']] = {
                    'cmd': msg['cmd'],
                    'stime': msg['stime'],
                    msg['done']: False
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
            res = requests.get(base_uri+'/status/' + job_id)
            if not res.ok:
                print('Error occurred while communicating with server!')
                sys.exit(1)
            msg = json.loads(res.text)
            if msg['done']:
                rcompcache.pop(job_id)
                with open(rcompcache_path, 'w') as fp:
                    json.dump(rcompcache, fp)
                job_output = msg['output'].strip()
                if len(job_output) > 0:
                    print(job_output)
            else:
                print('id: {}'.format(msg['id']))
            sys.exit(0)

        while not msg['done']:
            time.sleep(0.1)
            res = requests.get(base_uri+'/status/' + msg['id'])
            if not res.ok:
                print('Error occurred while communicating with server!')
                sys.exit(1)
            msg = json.loads(res.text)
        job_output = msg['output'].strip()
        if len(job_output) > 0:
            print(job_output)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
