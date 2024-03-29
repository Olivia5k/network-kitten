import sys
import os
import argparse
import logging
import subprocess as sub
import errno

from os.path import join
from os.path import dirname

from kitten import conf
from kitten import db
from kitten import node
from kitten import server
from kitten import log


def version():
    """
    Grab dynamic version info from git tags

    """

    git_dir = join(dirname(dirname(__file__)), '.git')
    if not os.path.exists(git_dir):
        logging.error(
            'git directory not found\n'
            'kitten uses git tags to determine versions\n'
            'Please get the source at https://github.com/thiderman/kitten\n'
        )
        return 'unknown'

    cmd = 'git --git-dir={0} describe --tag --abbrev --always --dirty'.format(
        git_dir,
    )
    proc = sub.Popen(cmd.split(), stdout=sub.PIPE, stderr=sub.PIPE)
    ret = proc.communicate()[0]

    if sys.version_info > (3,):  # pragma: nocover
        ret = ret.decode()

    ret = ret.strip()
    return ret


def global_arguments(parser):
    parser.add_argument(
        '--port',
        type=int,
        default=conf.DEFAULT_PORT,
        metavar='<port>',
        help='Port to listen on, default {0}'.format(conf.DEFAULT_PORT),
    )

    return parser


def main():
    # First things first; setup purdy color logging:
    log.setup_color()

    # Base of argument parser
    parser = argparse.ArgumentParser('kitten')
    parser = global_arguments(parser)
    subparsers = parser.add_subparsers(help="Core commands", dest="command")

    # Executors dict. All setup_parser functions are required add to this dict
    # with a key on parsers and value as functions that will handle the
    # resulting argparse namespace.
    executors = {
        'server': server.setup_parser(subparsers),
        'node': node.setup_parser(subparsers),
    }

    # Parse the current command line.
    ns = parser.parse_args()

    # No command specified. Print help and exit.
    if not ns.command:
        parser.print_help()
        sys.exit(errno.EINVAL)

    # Find out what port we will be using
    if not ns.port:
        ns.port = conf.PORT

    # Create application specific directories.
    conf.create_dirs()

    # Create core db tables that the application depends upon.
    db.setup_core(ns)

    # If the server is not already running and we're not trying to modify it,
    # start one in the background.
    if not server.is_running(ns) and ns.command != 'server':
        logging.info('Server not running. Starting in background.')
        sub.Popen([sys.argv[0], 'server'], stdout=sub.PIPE, stderr=sub.PIPE)

    # Send the namespace to the command handler so that it can actually execute
    # the specified command. Should return numeric exit code or None.
    ret = executors[ns.command](ns)

    sys.exit(ret)
