import jsonschema
import pytest

from itertools import product
from copy import deepcopy
from mock import MagicMock, patch

from kitten.server import KittenServer
from kitten.request import KittenRequest

from test.mocks import MockDatabaseMixin


class RequestMixin(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

        self.request_base = {
            'id': {
                'uuid': 'uuid-hehe-etc',
                'from': 'all of us',
                'to': 'all of you',
            },
            'paradigm': 'test',
            'method': 'test',
        }

        # Generate all four different request sets
        for k, p in product(('request', 'response'), ('init', 'payload')):
            data = deepcopy(self.request_base)
            data['id'].update({'kind': k, 'phase': p})
            setattr(self, '{0}_{1}'.format(k, p), data)


class TestRequestValidation(RequestMixin):
    def setup_method(self, method):
        self.request = {
            'hehe': 'fail',
            'paradigm': 'test',
            'method': 'test',
        }

    def test_handle_request_invalid_validation(self):
        request = KittenRequest(self.request)
        with pytest.raises(jsonschema.exceptions.ValidationError):
            request.process_request_payload()

    def test_handle_response_invalid_validation(self):
        request = KittenRequest(self.request)
        with pytest.raises(jsonschema.exceptions.ValidationError):
            request.process_response_payload()


class TestRequestProcess(RequestMixin):
    def setup_method(self, method):
        self.socket = MagicMock()
        super(TestRequestProcess, self).setup_method(method)

    def check_code(self, code, msg):
        check = {'code': code, 'message': msg}
        check.update(self.request_payload)
        self.socket.send_json.assert_called_once_with(check)

    @patch.object(KittenRequest, 'process_confirm')
    @patch.object(KittenRequest, 'process_request_payload')
    def test_process_request_payload(self, pr, pc):
        request = KittenRequest(self.request_payload)

        response = MagicMock()
        pr.return_value = response

        request.process(self.socket)

        pr.assert_called_once_with()
        self.socket.send_json.assert_called_once_with(response)
        self.socket.recv_json.assert_called_once_with()
        pc.assert_called_once_with(self.socket.recv_json.return_value)

    @patch.object(KittenRequest, 'process_request_payload')
    def test_process_validationerror(self, pr):
        request = KittenRequest(self.request_payload)

        msg = 'Hehehehee'
        pr.side_effect = jsonschema.exceptions.ValidationError(msg)
        request.process(self.socket)
        self.check_code('VALIDATION_ERROR', msg)

    @patch.object(KittenRequest, 'process_request_payload')
    def test_process_exception(self, process_request_payload):
        request = KittenRequest(self.request_payload)
        msg = '*giggles*'
        process_request_payload.side_effect = Exception(msg)
        request.process(self.socket)
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

        request = KittenRequest(data)
        request.paradigms = {p: paradigm}

        loads.return_value = data

        ret = request.process_request_payload()

        req.assert_called_once_with(data)
        paradigm.scale_response.assert_called_once_with(data)
        res.assert_called_once_with(response)
        assert ret == response


class TestRequestItem(MockDatabaseMixin):
    @patch('kitten.request.Session')
    @patch('kitten.request.KittenRequestItem')
    def test_save(self, kri, session):
        mreq, mres = MagicMock(), MagicMock()
        request = KittenRequest(mreq)
        request.response = mres

        request.save()

        kri.assert_called_once_with(sender='', request=mreq, response=mres)

        srv = session.return_value
        srv.add.assert_called_once_with(kri.return_value)
        srv.commit.assert_called_once_with()
        srv.close.assert_called_once_with()


class TestRequestHost(object):
    def setup_method(self, method):
        self.to = 'fire-and-ice'
        self._from = 'looking-for-a-stranger'
        self.data = {'id': {
            'kind': 'request',
            'to': self.to,
            'from': self._from,
        }}

    def test_req(self):
        request = KittenRequest(self.data)

        ret = request.host
        assert ret == 'tcp://{0}'.format(self.to)

    def test_res(self):
        self.data['id']['kind'] = 'response'
        request = KittenRequest(self.data)

        ret = request.host
        assert ret == 'tcp://{0}'.format(self._from)
