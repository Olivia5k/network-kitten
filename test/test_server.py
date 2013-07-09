import json
import jsonschema
import pytest

from wolf.server import WolfServer
from wolf.server import RequestException


class MockParadigm(object):
    def fake(self, request):
        return {
            'code': 'OK'
        }


class TestServerIntegration(object):
    def setup_method(self, method):
        self.server = WolfServer()
        self.server.paradigms = {
            'mock': MockParadigm()
        }

    def test_handle_request(self):
        request = json.dumps({'paradigm': 'mock', 'method': 'fake'})
        result = self.server.handle_request(request)

        assert result == {'code': 'OK'}

    def test_handle_request_invalid_json(self):
        request = '{'
        with pytest.raises(RequestException):
            self.server.handle_request(request)

    def test_handle_request_invalid_validation(self):
        request = json.dumps({'hehe': 'fail'})
        with pytest.raises(jsonschema.exceptions.ValidationError):
            self.server.handle_request(request)
