"""command-line interface (CLI)

For local development, use the `--rcomp-server` switch to direct this
client at the localhost. E.g.,

    rcomp --rcomp-server http://127.0.0.1:8000
"""
import argparse
import sys
import time
import json

import requests

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rcomp', add_help=False)
    parser.add_argument('--rcomp-help', action='store_true',
                        dest='show_help',
                        help='print this help message and exit')
    parser.add_argument('--rcomp-version', action='store_true',
                        dest='show_version',
                        help='print version number and exit')
    parser.add_argument('--rcomp-server', metavar='URI',
                        dest='base_uri',
                        help=('base URI for job requests.'
                              ' (default is https://api.fmtools.org)'))
    parser.add_argument('--rcomp-nonblocking', action='store_true',
                        dest='nonblocking', default=False,
                        help=('Default behavior is to wait for remote job'
                              ' to complete. Use this switch to immediately'
                              ' return after job successfully starts.'))
    parser.add_argument('--rcomp-continue', metavar='JOBID',
                        dest='job_id', default=None, nargs='?',
                        help='')
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

    if args.COMMAND is None:
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
        res = requests.get(base_uri+'/' + args.COMMAND)
        if not res.ok:
            print('Error occurred while sending initial request to the server!')
            sys.exit(1)
        msg = json.loads(res.text)
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
