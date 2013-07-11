import os
import errno

PORT = 5555


def get_dir(xdg_key, fallback):
    """
    Get wolf directories

    Try with the XDG standard if it exists.

    """

    # TODO: Windows.
    path = os.getenv(
        'XDG_{0}'.format(xdg_key),
        os.path.join(os.getenv('HOME'), fallback)
    )
    return os.path.join(path, 'wolf')


DATA_DIR = get_dir('DATA_HOME', '.local/share')
CACHE_DIR = get_dir('CACHE_HOME', '.cache')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
PIDFILE = os.path.join(CACHE_DIR, 'server.pid')


def create_dirs():
    for path in (DATA_DIR, CACHE_DIR, LOG_DIR):
        # Python 3.2 has os.makedirs(exist_ok=True)...
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
