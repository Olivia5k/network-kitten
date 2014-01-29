import re
from kitten.client import KittenClient


class Paradigm(object):
    client = KittenClient()

    def _get_paradigm_name(self):
        cls = self.__class__.__name__
        cls = cls.lower()
        cls = cls[:-8]  # Remove paradigm

        return cls


def annotate(func):
    def inner(self, *args):
        ret = func(self, *args)

        ret.update({
            'paradigm': self._get_paradigm_name(),
            'method': re.sub(r'_re(quest|sponse)$', '', func.__name__),
        })

        return ret
    return inner
