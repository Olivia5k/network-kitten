import pytest

from kitten.validation import Validator
from jsonschema.exceptions import ValidationError

from mock import MagicMock
from test import MockValidator


class TestValidatorGetMethod(object):
    def setup_method(self, method):
        self.validator = Validator()

    def test_get_method_no_paradigm(self):
        request = {'method': 'hehe'}
        with pytest.raises(ValidationError) as exc:
            self.validator.get_method(request)

        assert 'paradigm' in exc.value.message
        assert 'method' not in exc.value.message

    def test_get_method_no_method(self):
        request = {'paradigm': 'hehe'}
        with pytest.raises(ValidationError) as exc:
            self.validator.get_method(request)

        assert 'paradigm' not in exc.value.message
        assert 'method' in exc.value.message

    def test_get_method(self):
        p = 'wow'
        m = 'doge'
        request = {'paradigm': p, 'method': m}
        paradigm, method = self.validator.get_method(request)

        assert paradigm == p
        assert method == m


class TestValidatorRequest(object):
    def setup_method(self, method):
        self.validator = MockValidator()
        self.paradigm = MagicMock()
        self.paradigm.validator = self.validator
        self.paradigms = {'paradigm': self.paradigm}

        self.request = {
            'paradigm': 'paradigm',
            'method': 'method',
        }

    def test_no_paradigm(self):
        self.request['paradigm '] = "404"
        self.paradigms = {'hehe': True}

        with pytest.raises(ValidationError) as exc:
            self.validator.request(self.request, self.paradigms)

        assert 'hehe' in exc.value.message

    def test_no_method(self):
        method = 'fail'
        self.request['method'] = method

        with pytest.raises(ValidationError) as exc:
            self.validator.request(self.request, self.paradigms)

        assert method in exc.value.message

    def test_working_example(self):
        self.request['field'] = 1000
        self.validator.request(self.request, self.paradigms)

    def test_failing_example(self):
        self.request['field'] = 'helo i am string not number'

        with pytest.raises(ValidationError):
            self.validator.request(self.request, self.paradigms)


class TestValidatorGetKnownMethods(object):
    def setup_method(self, method):
        self.validator = MockValidator()

    def test_get_methods(self):
        ret = self.validator.get_known_methods()

        assert len(ret) == 1
        assert 'method' in ret

    def test_get_methods_add_one_more(self):
        def inner(self):
            pass

        self.validator.hehe_request = inner
        ret = self.validator.get_known_methods()

        assert len(ret) == 2
        assert 'method' in ret
        assert 'hehe' in ret

    def test_get_methods_add_one_more_not_callable(self):
        self.validator.hehe_request = 'ohnoes'
        ret = self.validator.get_known_methods()

        assert len(ret) == 1
        assert 'method' in ret
        assert 'hehe' not in ret
