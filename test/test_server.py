import json
import signal
import pytest

from mock import MagicMock, patch, call, mock_open
from test.utils import builtin

from kitten import server
from kitten.server import KittenServer
from kitten.server import setup_parser
from kitten.server import execute_parser
from kitten.request import KittenRequest


class TestServerIntegration(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    def test_handle_request(self):
        request = json.dumps({'paradigm': 'mock', 'method': 'method'})
        result = self.server.handle_request(request)

        assert result == {
            'ack': True,
        }


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

    @pytest.mark.skipif(True, reason='broken')
    @patch.object(server, 'KittenServer')
    def test_execute_parser_start_server(self, ks):
        self.ns.server_command = 'start'
        ks.return_value = self.server
        execute_parser(self.ns)

        ks.assert_called_once_with(self.ns)
        assert self.server.listen_forever.called

    @patch('os.path.exists')
    @patch('os.kill')
    def test_execute_parser_stop_server(self, kill, exists):
        pid = 9999
        self.ns.server_command = 'stop'
        exists.return_value = True

        fake = mock_open(read_data=str(pid))
        with patch(builtin('open'), fake, create=True):
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
        self.server.setup_signals = MagicMock()
        self.server.setup_pidfile = MagicMock()

    def test_full_setup_calls_setup_signals(self):
        self.server.setup()
        assert self.server.setup_signals.called

    def test_full_setup_calls_setup_pidfile(self):
        self.server.setup()
        assert self.server.setup_pidfile.called


class TestServerSetupUnits(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    @patch.object(signal, 'signal')
    def test_setup_signals(self, signal):
        self.server.setup_signals()

        assert signal.call_args_list == [
            call(2, self.server.signal_handler),
            call(15, self.server.signal_handler),
        ]

    @patch('os.getpid')
    def test_setup_pidfile(self, getpid):
        pid = 13337
        getpid.return_value = pid

        fake = mock_open()
        with patch(builtin('open'), fake):
            self.server.setup_pidfile()

        fake.return_value.write.assert_called_once_with(str(pid))


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

    @patch('kitten.conf.pidfile')
    @patch('os.remove')
    def test_teardown_pidfile(self, remove, pidfile):
        self.server.teardown_pidfile()
        remove.assert_called_once_with(pidfile.return_value)


class TestServerSocket(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    @patch('zmq.green.Context')
    def test_get_socket(self, Context):
        port = 3307
        self.server.ns.port = port
        ctx = MagicMock()
        Context.return_value = ctx

        ret = self.server.get_socket()
        socket = ctx.socket()

        assert ret is socket
        socket.bind.assert_called_once_with('tcp://*:{0}'.format(port))


class TestServerListen(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
        self.socket = MagicMock()

    def test_listen(self):
        recv = 'lel'
        fake = {}
        self.socket.recv_unicode = MagicMock(return_value=recv)
        self.server.handle_request = MagicMock(return_value=fake)

        self.server.listen(self.socket)
        self.socket.recv_unicode.assert_called_once_with()
        self.server.handle_request.assert_called_once_with(recv)
        self.socket.send_unicode.assert_called_once_with('{}')


class TestServerUtils(object):
    @patch('kitten.conf.pidfile')
    @patch('os.path.isfile')
    def test_is_running(self, isfile, pidfile):
        ns = MagicMock()
        ns.port = 18237

        server.is_running(ns)
        isfile.assert_called_once_with(pidfile.return_value)


class TestServerQueue(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    def test_handle_puts_requests_in_queue(self):
        data = '{}'
        ret = self.server.handle_request(data)

        assert self.server.queue.qsize() == 1
        assert self.server.queue.get() == KittenRequest(data)
        assert ret == {'ack': True}


class TestServerWorker(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    def test_handle_request_and_exit(self):
        request, pool = MagicMock(), MagicMock()
        sock_ret = 'sex as a weapon'
        get_socket = MagicMock(return_value=sock_ret)

        self.server.get_socket = get_socket
        self.server.pool = pool
        self.server.queue = MagicMock()
        self.server.queue.empty = MagicMock(return_value=False)
        self.server.queue.get = MagicMock(side_effect=[request, None])

        assert self.server.working is None
        self.server.work()

        self.server.pool.spawn.assert_called_once_with(
            request.process,
            sock_ret,
        )
        self.server.pool.join.assert_called_once_with()
        assert self.server.working is False
