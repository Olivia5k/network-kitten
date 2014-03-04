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
        request = {'paradigm': 'mock', 'method': 'method'}
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

    @patch.object(server, 'KittenServer')
    def test_execute_parser_start_server(self, ks):
        self.ns.server_command = 'start'
        ks.return_value = self.server
        execute_parser(self.ns)

        ks.assert_called_once_with(self.ns)
        self.server.start.assert_called_once_with()

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


class TestServerTeardown(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    @patch('sys.exit')
    def test_teardown(self, exit):
        self.server.teardown_pidfile = MagicMock()
        self.server.teardown_listener = MagicMock()
        self.server.teardown_workers = MagicMock()
        self.server.teardown()

        self.server.teardown_pidfile.assert_called_once_with()
        self.server.teardown_listener.assert_called_once_with()
        self.server.teardown_workers.assert_called_once_with()
        exit.assert_called_once_with(0)

    @patch('sys.exit')
    def test_teardown_without_exit(self, exit):
        self.server.teardown_pidfile = MagicMock()
        self.server.teardown_listener = MagicMock()
        self.server.teardown_workers = MagicMock()
        self.server.teardown(False)

        assert not exit.called

    @patch('kitten.conf.pidfile')
    @patch('os.remove')
    def test_teardown_pidfile(self, remove, pidfile):
        self.server.teardown_pidfile()
        remove.assert_called_once_with(pidfile.return_value)

    def test_teardown_listener(self):
        self.server.listener = MagicMock()
        self.server.teardown_listener()
        self.server.listener.kill.assert_called_once_with(timeout=5)


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

        self.server.get_socket = self.socket
        self.server.teardown = MagicMock()

    def test_listen(self):
        recv = {'pat': 'benatar'}
        fake = {}
        self.socket.recv_json = MagicMock(return_value=recv)
        self.server.handle_request = MagicMock(return_value=fake)

        self.server.listen(self.socket)
        self.socket.recv_json.assert_called_once_with()
        self.server.handle_request.assert_called_once_with(recv)
        self.socket.send_json.assert_called_once_with({})

    def test_listen_forever(self):
        self.server.listen = MagicMock(side_effect=[True, True, False])
        self.server.listen_forever()

        assert self.server.listen.call_count == 3
        self.server.teardown.assert_called_once_with()

    def test_listen_forever_exception(self):
        self.server.listen = MagicMock(side_effect=[True, True, Exception])
        self.server.log = MagicMock()
        self.server.listen_forever()

        assert self.server.listen.call_count == 3
        assert self.server.log.exception.call_count == 1
        self.server.teardown.assert_called_once_with()


class TestServerUtils(object):
    def setup_method(self, method):
        self.ns = MagicMock()
        self.ns.port = 18237
        self.pid = 1209

    @patch('kitten.conf.pidfile')
    @patch('os.path.isfile')
    def test_is_running_no_pidfile(self, isfile, pidfile):
        fake = mock_open(read_data=str(self.pid))
        isfile.return_value = False

        with patch(builtin('open'), fake):
            ret = server.is_running(self.ns)

        isfile.assert_called_once_with(pidfile.return_value)
        assert ret is False

    @patch('kitten.conf.pidfile')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_is_running_pidfile_but_no_dir(self, isfile, isdir, pidfile):
        fake = mock_open(read_data=str(self.pid))
        isfile.return_value = True
        isdir.return_value = False

        with patch(builtin('open'), fake):
            ret = server.is_running(self.ns)

        isfile.assert_called_once_with(pidfile.return_value)
        isdir.assert_called_once_with('/proc/{0}'.format(self.pid))
        assert ret is False

    @patch('kitten.conf.pidfile')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_is_running_pidfile_and_dir(self, isfile, isdir, pidfile):
        fake = mock_open(read_data=str(self.pid))
        isfile.return_value = True
        isdir.return_value = True

        with patch(builtin('open'), fake):
            ret = server.is_running(self.ns)

        isfile.assert_called_once_with(pidfile.return_value)
        isdir.assert_called_once_with('/proc/{0}'.format(self.pid))
        assert ret is True


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
        self.server.queue = MagicMock()
        self.server.queue.empty = MagicMock(return_value=False)
        self.server.pool = MagicMock()
        self.server.get_socket = MagicMock()

    @patch('gevent.sleep')
    def test_empty_queue(self, sleep):
        self.server.queue.empty.return_value = True
        ret = self.server.work()

        assert ret is True
        sleep.assert_called_once_with(1.0)

    def test_handle_request(self):
        request = MagicMock()
        sock_ret = 'sex as a weapon'
        self.server.get_socket.return_value = sock_ret
        self.server.queue.get.return_value = request

        ret = self.server.work()

        assert ret is True
        self.server.pool.spawn.assert_called_once_with(
            request.process,
            sock_ret,
        )


class TestServerWorkerLoop(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    def test_working(self):
        # This is semi-inconvenient, but it's the only smooth way to check that
        # the state has changed. Infinite loops and all that jazz.
        assert self.server.working is None
        self.server.work = MagicMock(side_effect=Exception)
        with pytest.raises(Exception):
            self.server.work_forever()

        self.server.work.assert_called_once_with()
        assert self.server.working is True

    def test_stop_working(self):
        assert self.server.working is None
        self.server.work = MagicMock(return_value=None)
        self.server.work_forever()

        self.server.work.assert_called_once_with()
        assert self.server.working is False


class TestServerWorkerTeardown(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())
        self.server.pool = MagicMock()

    def test_teardown_no_workers_running(self):
        self.server.pool.size = 12
        self.server.pool.free_count.return_value = self.server.pool.size
        ret = self.server.teardown_workers()

        assert ret is True

    def test_teardown_workers_running(self):
        self.server.pool.size = 12
        self.server.pool.free_count.return_value = 1
        ret = self.server.teardown_workers()

        assert ret is None
        self.server.pool.kill.assert_called_once_with(timeout=5)


class TestServerStartStop(object):
    def setup_method(self, method):
        self.server = KittenServer(MagicMock())

    @patch('gevent.spawn')
    def test_start(self, spawn):
        self.server.setup = MagicMock()

        ret = self.server.start()

        assert ret is spawn.return_value
        self.server.setup.assert_called_once_with()
