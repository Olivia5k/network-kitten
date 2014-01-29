import re
from kitten.client import KittenClient


class Paradigm(object):
    client = KittenClient()

    def send(self, address, request):
        paradigms = {self.name: self}

        self.validator.request(request, paradigms)
        response = self.client.send(address, request)
        self.validator.response(response, paradigms)

        return response

    @property
    def name(self):
        # 'FooParadigm' => 'foo'
        return self.__class__.__name__.lower()[:-8]  # Remove paradigm


def annotate(func):
    def inner(self, *args):
        ret = func(self, *args)

        ret.update({
            'paradigm': self.name,
            'method': re.sub(r'_re(quest|sponse)$', '', func.__name__),
        })

        return ret
    return inner
