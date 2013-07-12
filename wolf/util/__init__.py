import os
import errno


def mkdir(path):
    """
    Safe implementation of 'mkdir -p'

    """

    # Python 3.2 has os.makedirs(exist_ok=True)...
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
