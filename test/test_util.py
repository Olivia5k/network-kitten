from kitten.util import AutoParadigmMixin


class TestAutoParadigmMixin(object):
    def setup_method(self, method):
        self.apm = AutoParadigmMixin()

    def test_first_load(self):
        ret = self.apm.paradigms

        assert 'node' in ret
        assert 'node' in self.apm._paradigms

    def test_second_load(self):
        self.apm._paradigms = {'hehe': True}
        ret = self.apm.paradigms

        assert 'hehe' in ret
        assert 'hehe' in self.apm._paradigms
