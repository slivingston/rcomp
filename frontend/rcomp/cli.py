"""command-line interface (CLI)

For local development, use the `-s` switch to direct this client at
the localhost. E.g.,

    rcomp -s http://127.0.0.1:8000
"""
import argparse
import sys

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rcomp', add_help=False)
    parser.add_argument('--rcomp-help', action='store_true', dest='show_help',
                        help='print this help message and exit')
    parser.add_argument('--rcomp-version', action='store_true', dest='show_version',
                        help='print version number and exit')
    parser.add_argument('--rcomp-server', metavar='URI', dest='basi_uri',
                        help='base URI for job requests. (default is https://api.fmtools.org)')
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

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
