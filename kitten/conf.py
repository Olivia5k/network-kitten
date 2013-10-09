import os

from kitten import util

PORT = 5555


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
DB_URI = 'sqlite:///{0}/kitten.db'.format(DATA_DIR)


def create_dirs():
    for path in (DATA_DIR, CACHE_DIR, LOG_DIR):
        util.mkdir(path)
