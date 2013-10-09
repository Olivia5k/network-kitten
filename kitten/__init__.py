import sys
import argparse
import logging
import subprocess as sub

from wolf import conf
from wolf import db
from wolf import connections
from wolf import server
from wolf import log


def main():
    # First things first; setup purdy color logging:
    log.setup_color()

    # Base of argument parser
    parser = argparse.ArgumentParser('wolf')
    subparsers = parser.add_subparsers(help="Core commands", dest="command")

    # Executors dict. All setup_parser functions are required add to this dict
    # with a key on parsers and value as functions that will handle the
    # resulting argparse namespace.
    subparsers.executors = {}

    # Run core argparse setups.
    server.setup_parser(subparsers)
    connections.setup_parser(subparsers)

    # Parse the current command line.
    ns = parser.parse_args()

    # No command specified. Print help and exit.
    if not ns.command:
        parser.print_help()
        sys.exit(0)

    # Create application specific directories.
    conf.create_dirs()

    # Create core db tables that the application depends upon.
    db.setup_core()

    # If the server is not already running and we're not trying to modify it,
    # start one in the background.
    if not server.is_running() and ns.command != 'server':
        logging.info('Server not running. Starting in background.')
        sub.Popen([sys.argv[0], 'server'], stdout=sub.PIPE, stderr=sub.PIPE)

    # Send the namespace to the command handler so that it can actually execute
    # the specified command. Should return numeric exit code or None.
    ret = subparsers.executors[ns.command](ns)

    sys.exit(ret)
