import json
import jsonschema
import pytest

from mock import MagicMock, patch

from kitten.server import KittenServer
from kitten.request import RequestError
from kitten.request import KittenRequest


class RequestMixin(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())


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


class TestRequestHandle(RequestMixin):
    @patch('json.loads')
    @patch.object(KittenRequest, 'paradigms')
    @patch.object(KittenRequest, 'validate_response')
    @patch.object(KittenRequest, 'validate_request')
    def test_handle(self, req, res, para, loads):
        p, m = 'banana', 'scale'
        data = {'paradigm': p, 'method': m}
        response = {'haha': 'fak u'}
        paradigm = MagicMock()
        paradigm.scale_response.return_value = response

        request = KittenRequest('{}')
        request.paradigms = {p: paradigm}

        loads.return_value = data

        ret = request.handle()

        req.assert_called_once_with(data)
        paradigm.scale_response.assert_called_once_with(data)
        res.assert_called_once_with(response)
        assert ret == response


class TestRequestProperty(RequestMixin):
    """
    Test the self.request property

    """

    @patch('json.loads')
    def test_cache(self, loads):
        fake = MagicMock()
        request = KittenRequest('')
        request._request = fake
        assert request.request is fake
        assert loads.call_count == 0

    @patch('json.loads')
    def test_exception(self, loads):
        request = KittenRequest('')
        loads.side_effect = ValueError

        assert request.exception is None
        ret = request.request
        assert ret is None
        assert request.exception[0] is RequestError
        assert request.exception[1] == "INVALID_REQUEST"

    def test_loading(self):
        request = KittenRequest('{"lel": true}')
        ret = request.request
        assert ret == {'lel': True}
        assert request.exception is None
