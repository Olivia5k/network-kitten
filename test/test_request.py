import jsonschema
import pytest

from mock import MagicMock, patch

from kitten.server import KittenServer
from kitten.request import KittenRequest

from test.mocks import MockDatabaseMixin


class RequestMixin(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())


class TestRequestValidation(RequestMixin):
    def test_handle_request_invalid_validation(self):
        request = KittenRequest({"hehe": "fail"})
        with pytest.raises(jsonschema.exceptions.ValidationError):
            request.process_request()


class TestRequestProcess(RequestMixin):
    def setup_method(self, method):
        self.socket = MagicMock()
        self.dry_request = {
            'id': {
                'uuid': 'uuid-hehe-etc',
                'from': 'all of us',
                'to': 'all of you',
                'kind': 'request',
            },
            'paradigm': 'test',
            'method': 'test',
        }
        self.request = KittenRequest(self.dry_request)
        super(TestRequestProcess, self).setup_method(method)

    def check_code(self, code, msg):
        check = {'code': code, 'message': msg}
        check.update(self.dry_request)
        self.socket.send_json.assert_called_once_with(check)

    @patch.object(KittenRequest, 'process_confirm')
    @patch.object(KittenRequest, 'process_request')
    def test_process(self, pr, pc):
        response = MagicMock()
        pr.return_value = response

        self.request.process(self.socket)

        pr.assert_called_once_with()
        self.socket.send_json.assert_called_once_with(response)
        self.socket.recv_json.assert_called_once_with()
        pc.assert_called_once_with(self.socket.recv_json.return_value)

    @patch.object(KittenRequest, 'process_request')
    def test_process_validationerror(self, pr):
        msg = 'Hehehehee'
        pr.side_effect = jsonschema.exceptions.ValidationError(msg)
        self.request.process(self.socket)
        self.check_code('VALIDATION_ERROR', msg)

    @patch.object(KittenRequest, 'process_request')
    def test_process_exception(self, process_request):
        msg = '*giggles*'
        process_request.side_effect = Exception(msg)
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

        request = KittenRequest(data)
        request.paradigms = {p: paradigm}

        loads.return_value = data

        ret = request.process_request()

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
            'kind': 'req',
            'to': self.to,
            'from': self._from,
        }}

    def test_req(self):
        request = KittenRequest(self.data)

        ret = request.host
        assert ret == 'tcp://{0}'.format(self.to)

    def test_res(self):
        self.data['id']['kind'] = 'res'
        request = KittenRequest(self.data)

        ret = request.host
        assert ret == 'tcp://{0}'.format(self._from)
