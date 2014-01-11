from kitten.node import Node
from kitten.node import setup_parser
from kitten.node import execute_parser
from test import MockDatabaseMixin

from mock import MagicMock, patch


class NodeUtilMixin(object):
    def add_node(self, address, port, display_name):
        node = Node(address, port, display_name)
        self.session.add(node)
        self.session.commit()


class TestNodeCreation(MockDatabaseMixin):
    def test_create_node(self):
        Node.create('localhost', 65535)

        res = self.session.query(Node).all()

        assert len(res) == 1
        assert res[0].address == "localhost"
        assert res[0].port == 65535

    def test_create_node_with_display_name(self):
        Node.create('localhost', 65535, 'gooby')

        res = self.session.query(Node).all()

        assert len(res) == 1
        assert res[0].display_name == 'gooby'


class TestNodeArgparser(object):
    def setup_method(self, method):
        self.subparsers = MagicMock()

    def test_setup_parser_sets_up_node_namespace(self):
        ret = setup_parser(self.subparsers)
        assert ret.add_parser.call_args[0][0] == 'node'

    def test_setup_parser_sets_up_executor(self):
        self.subparsers.executors = {}
        ret = setup_parser(self.subparsers)
        assert ret.executors == {
            'node': execute_parser
        }


class TestNodeArgparserIntegration(MockDatabaseMixin, NodeUtilMixin):
    def setup_method(self, method):
        self.ns = MagicMock()
        super(TestNodeArgparserIntegration, self).setup_method(method)

    @patch.object(Node, 'list')
    def test_execute_no_arguments(self, l):
        self.ns.sub = None
        execute_parser(self.ns)

        assert l.called

    @patch.object(Node, 'repr')
    def test_execute_list_argument(self, r):
        self.ns.sub = 'list'
        self.ns.filter = None

        self.add_node('add', 'port', 'foo')
        self.add_node('add', 'port', 'bar')

        execute_parser(self.ns)

        assert r.call_count == 2

    @patch.object(Node, 'repr')
    def test_execute_list_argument_with_filter(self, r):
        self.ns.sub = 'list'
        self.ns.filter = 'bar'

        self.add_node('add', 'port', 'foo')
        self.add_node('add', 'port', 'bar')

        execute_parser(self.ns)

        assert r.call_count == 1

    @patch.object(Node, 'repr')
    def test_execute_add_argument(self, r):
        ip = '123.123.123.123'
        port = 1234
        display_name = 'hax0r tester'

        self.ns.sub = 'add'
        self.ns.ip = ip
        self.ns.port = port
        self.ns.display_name = display_name

        execute_parser(self.ns)

        res = self.session.query(Node).all()
        assert len(res) == 1
        assert res[0].address == ip
        assert res[0].port == port
        assert res[0].display_name == display_name
