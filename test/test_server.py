import json
import jsonschema
import pytest
import signal
import zmq

from mock import MagicMock, patch, call, mock_open
from test import utils

from kitten import server
from kitten.server import KittenServer
from kitten.server import RequestException
from kitten.server import setup_parser
from kitten.server import execute_parser


class MockParadigm(object):
    def fake(self, request):
        return {
            'code': 'OK'
        }


class TestServerIntegration(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
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

    @pytest.mark.xfail  # Until actual validation is back in place
    def test_handle_request_invalid_validation(self):
        request = json.dumps({'hehe': 'fail'})
        with pytest.raises(jsonschema.exceptions.ValidationError):
            self.server.handle_request(request)


class TestServerArgparser(object):
    def setup_method(self, method):
        self.subparsers = MagicMock()

    def test_setup_parser_sets_up_server_namespace(self):
        setup_parser(self.subparsers)
        # Only check the first argument; a change to the help text should not
        # make the test fail.
        assert self.subparsers.add_parser.call_args[0][0] == 'server'

    def test_setup_parser_sets_up_executor(self):
        ret = setup_parser(self.subparsers)
        assert ret is execute_parser


class TestServerArgparserSubcommandSetup(object):
    def setup_method(self, method):
        self.server_args = MagicMock()
        self.sub_args = MagicMock()
        self.server_args.add_subparsers.return_value = self.sub_args

        self.subparsers = MagicMock()
        self.subparsers.add_parser.return_value = self.server_args

    def test_setup_parser_sets_up_start_command(self):
        setup_parser(self.subparsers)
        assert self.sub_args.add_parser.call_args_list[0][0][0] == 'start'

    def test_setup_parser_sets_up_stop_command(self):
        setup_parser(self.subparsers)
        assert self.sub_args.add_parser.call_args_list[1][0][0] == 'stop'


class TestServerArgparserIntegration(object):
    def setup_method(self, method):
        self.server = MagicMock()
        self.ns = MagicMock()

    @patch.object(server, 'KittenServer')
    def test_execute_parser_start_server(self, KS):
        self.ns.server_command = 'start'
        self.KittenServer = KS
        self.KittenServer.return_value = self.server
        execute_parser(self.ns)

        assert self.KittenServer.called
        assert self.server.listen_forever.called

    @patch('os.path.exists')
    @patch('os.kill')
    def test_execute_parser_stop_server(self, kill, exists):
        pid = 9999
        self.ns.server_command = 'stop'
        exists.return_value = True

        fake = mock_open(read_data=str(pid))
        with patch(utils.builtin('open'), fake, create=True):
            ret = execute_parser(self.ns)

        kill.assert_called_once_with(pid, signal.SIGINT)
        assert ret == 0

    @patch('os.path.exists')
    @patch('os.kill')
    def test_execute_parser_stop_server_no_pidfile(self, kill, exists):
        """
        This will effectively check if it works to stop the server when it is
        not running.

        """

        self.ns.server_command = 'stop'
        exists.return_value = False
        ret = execute_parser(self.ns)

        kill.call_count == 0
        assert ret == 1


class TestServerSetupIntegration(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
        self.server.setup_paradigms = MagicMock()
        self.server.setup_signals = MagicMock()
        self.server.setup_pidfile = MagicMock()

    def test_full_setup_calls_setup_paradigms(self):
        self.server.setup()
        assert self.server.setup_paradigms.called

    def test_full_setup_calls_setup_signals(self):
        self.server.setup()
        assert self.server.setup_signals.called

    def test_full_setup_calls_setup_pidfile(self):
        self.server.setup()
        assert self.server.setup_pidfile.called


class TestServerSetupUnits(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    def test_setup_paradigms(self):
        pmock = MagicMock()
        self.server.get_paradigms = MagicMock()
        self.server.get_paradigms.return_value = {'mock': pmock}

        self.server.setup_paradigms()
        assert pmock.setup.called

    @patch.object(signal, 'signal')
    def test_setup_signals(self, signal):
        self.server.setup_signals()

        assert signal.call_args_list[0] == call(2, self.server.signal_handler)
        assert signal.call_args_list[1] == call(15, self.server.signal_handler)

    @patch('os.getpid')
    def test_setup_pidfile(self, getpid):
        pid = 13337
        getpid.return_value = pid

        fake = mock_open()
        with patch(utils.builtin('open'), fake):
            self.server.setup_pidfile()

        assert fake.return_value.write.called_once_with(str(pid))


class TestServerSignalHandling(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
        self.server.teardown = MagicMock()

    def test_signal_handler_calls_teardown(self):
        self.server.signal_handler(2, MagicMock())
        assert self.server.teardown.called


class TestServerTeardownIntegration(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
        self.server.teardown_pidfile = MagicMock()

    def test_teardown_when_not_torn_down(self):
        assert not self.server.torn
        self.server.teardown()

        assert self.server.torn
        assert self.server.teardown_pidfile.called

    def test_teardown_when_already_torn_down(self):
        self.server.torn = True
        self.server.teardown()

        assert self.server.torn
        assert not self.server.teardown_pidfile.called


class TestServerTeardownUnits(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    @patch('kitten.conf.PIDFILE')
    @patch('os.remove')
    def test_teardown_pidfile(self, remove, pidfile):
        self.server.teardown_pidfile()
        assert remove.called_once_with(pidfile)


class TestServerSocket(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    @patch('zmq.Context')
    def test_get_socket(self, Context):
        port = 3307
        ctx = MagicMock()
        Context.return_value = ctx

        ret = self.server.get_socket(port)
        socket = ctx.socket()

        assert ret is socket
        assert socket.bind.called_once_with('tcp://*:{0}'.format(port))


class TestServerSocketListener(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
        self.server.handle_request = MagicMock()
        self.socket = MagicMock()

    def test_socket_interruption(self):
        self.socket.recv_unicode.side_effect = zmq.error.ZMQError

        ret = self.server.listen(self.socket)
        assert not ret, "Loop continued when it shouldn't"

    def test_request_exception(self):
        code, msg = 'TEST_ERROR', '#yolo'
        self.server.handle_request.side_effect = RequestException(code, msg)

        ret = self.server.listen(self.socket)
        assert ret, "Loop halted because of exception when it shouldn't"
        self.socket.send_unicode.called_once_with(
            json.dumps({'code': code, 'message': msg})
        )

    def test_validation_exception(self):
        msg = 'lel ur valiation suck'
        exc = jsonschema.exceptions.ValidationError(msg)
        self.server.handle_request.side_effect = exc

        ret = self.server.listen(self.socket)
        assert ret, "Loop halted because of exception when it shouldn't"
        self.socket.send_unicode.called_once_with(
            json.dumps({'code': 'VALIDATION_ERROR', 'message': msg})
        )

    def test_general_exception(self):
        msg = 'random hax0r error :('
        self.server.handle_request.side_effect = Exception(msg)

        ret = self.server.listen(self.socket)
        assert ret, "Loop halted because of exception when it shouldn't"
        self.socket.send_unicode.called_once_with(
            json.dumps({'code': 'UNKNOWN_ERROR', 'message': msg})
        )


class TestServerUtils(object):
    @patch('kitten.conf.PIDFILE')
    @patch('os.path.isfile')
    def test_is_running(self, isfile, pidfile):
        server.is_running()
        assert isfile.called_once_with(pidfile)
