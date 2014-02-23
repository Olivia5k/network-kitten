import os
import errno


def mkdir(path):  # pragma: nocover
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


class AutoParadigmMixin(object):
    """
    Helper mixin that automatically gets paradigms when self.paradigms is
    accessed.

    """

    _paradigms = {}

    @property
    def paradigms(self):
        if self._paradigms:
            return self._paradigms

        # TODO: Dynamic finding of paradigms
        from kitten.node import NodeParadigm
        self._paradigms = {
            'node': NodeParadigm()
        }
        return self._paradigms
