import jsonschema
import pytest

from mock import MagicMock
from test.utils import MockParadigm

from kitten.server import KittenServer
from kitten.request import RequestError
from kitten.request import KittenRequest
from kitten.validation import Validator


class TestRequestValidation(object):
    def setup_method(self, method):
        self.validator = Validator()
        self.server = KittenServer(MagicMock(), self.validator)
        self.paradigms = {
            'mock': MockParadigm()
        }

    def test_handle_request_invalid_json(self):
        request = KittenRequest('{')
        with pytest.raises(RequestError):
            request.handle()

    def test_handle_request_invalid_validation(self):
        request = KittenRequest('{"hehe": "fail"}')
        with pytest.raises(jsonschema.exceptions.ValidationError):
            request.handle()
