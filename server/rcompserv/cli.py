import argparse
import sys

from . import __version__
from .serv import Server


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rcompserv')
    parser.add_argument('-V', '--version', action='store_true',
                        dest='show_version',
                        help='print version number and exit')
    parser.add_argument('-t', '--timeout', metavar='T',
                        dest='timeout', type=int,
                        help=('maximum duration (seconds) of jobs;'
                              ' if 0, then no timeout restriction is used;'
                              ' default behavior is no timeout.'))
    parser.add_argument('--port',
                        dest='port',
                        type=int,
                        default=8080,
                        help='port on which to listen; default is 8080')
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.show_version:
        print('rcompserv '+__version__)
        return 0

    Server(port=args.port, timeout_per_job=args.timeout).run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
