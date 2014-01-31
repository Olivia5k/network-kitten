import os

from kitten import util

PORT = 5555
DEFAULT_PORT = 5555

ADDRESS = 'localhost'


def get_dir(xdg_key, fallback):
    """
    Get kitten directories

    Try with the XDG standard if it exists.

    """

    # TODO: Windows.
    path = os.getenv(
        'XDG_{0}'.format(xdg_key),
        os.path.join(os.getenv('HOME'), fallback)
    )
    return os.path.join(path, 'kitten')


DATA_DIR = get_dir('DATA_HOME', '.local/share')
CACHE_DIR = get_dir('CACHE_HOME', '.cache')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
PIDFILE = os.path.join(CACHE_DIR, 'server.pid')


def create_dirs():  # pragma: nocover
    for path in (DATA_DIR, CACHE_DIR, LOG_DIR):
        util.mkdir(path)
