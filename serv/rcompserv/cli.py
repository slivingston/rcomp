import argparse
import sys

from . import __version__
from .serv import Server


def main(argv=None):
    parser = argparse.ArgumentParser(prog='rcompserv')
    parser.add_argument('-V', '--version', action='store_true',
                        dest='show_version',
                        help='print version number and exit')
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.show_version:
        print('rcompserv '+__version__)
        return 0

    Server().run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
