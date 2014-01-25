import pytest
import errno

from kitten import main
from mock import patch
from mock import MagicMock


class TestMain(object):
    """
    These tests will test the order and succession of the projects main()

    By nature, these tests are very mocked out since they are not supposed
    to be starting anything at all.

    """

    def setup_method(self, method):
        self.parser = MagicMock()
        self.ns = MagicMock()
        self.parser.parse_args.return_value = self.ns
        self.runner = MagicMock()

    @patch('argparse.ArgumentParser')
    @patch('kitten.log')
    @patch('kitten.server')
    @patch('kitten.node')
    @patch('kitten.db')
    @patch('kitten.conf')
    def test_setup_no_args(self, conf, db, node, server, log, ap):
        ap.return_value = self.parser
        self.ns.command = None

        with pytest.raises(SystemExit) as exc:
            main()

        assert exc.value.code == errno.EINVAL
        assert log.setup_color.called
        assert self.parser.print_help.called

    @patch('sys.argv')
    @patch('argparse.ArgumentParser')
    @patch('kitten.log')
    @patch('kitten.server')
    @patch('kitten.node')
    @patch('kitten.db')
    @patch('kitten.conf')
    def test_setup_server_arg(self, conf, db, node, server, log, ap, av):
        command = 'server'
        argv = ['python', command]
        exit = 1000

        ap.return_value = self.parser
        av.return_value = argv
        self.ns.command = command

        server.setup_parser.return_value = self.runner
        self.runner.return_value = exit

        with pytest.raises(SystemExit) as exc:
            main()

        assert exc.value.code == exit
        assert log.setup_color.called
        assert conf.create_dirs.called
        assert db.setup_core.called

    @patch('subprocess.Popen')
    @patch('sys.argv')
    @patch('argparse.ArgumentParser')
    @patch('kitten.log')
    @patch('kitten.server')
    @patch('kitten.node')
    @patch('kitten.db')
    @patch('kitten.conf')
    def test_setup_server_autostart(
        self, conf, db, node, server, log, ap, av, popen
    ):
        command = 'node'
        argv = ['python', command]
        exit = 1000

        ap.return_value = self.parser
        av.return_value = argv
        self.ns.command = command

        server.is_running.return_value = False
        node.setup_parser.return_value = self.runner
        self.runner.return_value = exit

        with pytest.raises(SystemExit) as exc:
            main()

        assert exc.value.code == exit
        assert log.setup_color.called
        assert conf.create_dirs.called
        assert db.setup_core.called

        assert popen.called
