import json
import jsonschema
import pytest

from mock import MagicMock, patch

from kitten.server import KittenServer
from kitten.request import RequestError
from kitten.request import KittenRequest
from kitten.validation import Validator


class RequestMixin(object):
    def setup_method(self, method):
        self.validator = Validator()
        self.server = KittenServer(MagicMock(), self.validator)


class TestRequestValidation(RequestMixin):
    def test_handle_request_invalid_json(self):
        request = KittenRequest('{')
        with pytest.raises(RequestError):
            request.handle()

    def test_handle_request_invalid_validation(self):
        request = KittenRequest('{"hehe": "fail"}')
        with pytest.raises(jsonschema.exceptions.ValidationError):
            request.handle()


class TestRequestProcess(RequestMixin):
    def setup_method(self, method):
        self.socket = MagicMock()
        self.request = KittenRequest('{}')
        super(TestRequestProcess, self).setup_method(method)

    def check_code(self, code, msg):
        check = json.dumps({'code': code, 'message': msg})
        self.socket.send_unicode.assert_called_once_with(check)

    @patch('json.dumps')
    @patch.object(KittenRequest, 'handle')
    def test_process(self, handle, dumps):
        response = MagicMock()
        dummy = 'liz'
        dumps.return_value = dummy
        handle.return_value = response

        self.request.process(self.socket)

        handle.assert_called_once_with()
        dumps.assert_called_once_with(response)
        self.socket.send_unicode.assert_called_once_with(dummy)

    @patch.object(KittenRequest, 'handle')
    def test_process_requesterror(self, handle):
        code, msg = 'CODE', 'msg'
        handle.side_effect = RequestError(code, msg)
        self.request.process(self.socket)
        self.check_code(code, msg)

    @patch.object(KittenRequest, 'handle')
    def test_process_validationerror(self, handle):
        msg = 'Hehehehee'
        handle.side_effect = jsonschema.exceptions.ValidationError(msg)
        self.request.process(self.socket)
        self.check_code('VALIDATION_ERROR', msg)

    @patch.object(KittenRequest, 'handle')
    def test_process_exception(self, handle):
        msg = '*giggles*'
        handle.side_effect = Exception(msg)
        self.request.process(self.socket)
        self.check_code('UNKNOWN_ERROR', msg)
