import os
import errno
import logbook


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

    log = logbook.Logger('AutoParadigmMixin')
    _paradigms = {}

    def get_paradigms(self):
        if self._paradigms:
            return self._paradigms

        # TODO: Dynamic finding of paradigms
        from kitten.node import NodeParadigm
        self._paradigms = {
            'node': NodeParadigm()
        }
        return self._paradigms

    def set_paradigms(self, paradigms):
        self.log.debug('Overriding paradigms with {0}'.format(paradigms))
        self._paradigms = paradigms
        return self._paradigms

    paradigms = property(get_paradigms, set_paradigms)
