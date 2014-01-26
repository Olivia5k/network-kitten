from kitten.node import Node
from kitten.node import setup_parser
from kitten.node import execute_parser
from test import MockDatabaseMixin

from mock import MagicMock, patch


class NodeUtilMixin(object):
    def add_node(self, address):
        node = Node(address)
        self.session.add(node)
        self.session.commit()


class TestNodeCreation(MockDatabaseMixin):
    @patch.object(Node, 'ping')
    def test_create_node(self, p):
        p.return_value = True
        Node.create('localhost:65535')

        res = self.session.query(Node).all()

        assert len(res) == 1
        assert res[0].address == "localhost:65535"

    @patch.object(Node, 'ping')
    def test_create_node_ping_fails(self, p):
        p.return_value = False
        Node.create('localhost:65535')

        res = self.session.query(Node).all()

        assert len(res) == 0


class TestNodeArgparser(object):
    def setup_method(self, method):
        self.subparsers = MagicMock()

    def test_setup_parser_sets_up_node_namespace(self):
        setup_parser(self.subparsers)
        assert self.subparsers.add_parser.call_args[0][0] == 'node'

    def test_setup_parser_sets_up_executor(self):
        ret = setup_parser(self.subparsers)
        assert ret is execute_parser


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

        self.add_node('foo')
        self.add_node('bar')

        execute_parser(self.ns)

        assert r.call_count == 2

    @patch.object(Node, 'repr')
    def test_execute_list_argument_with_filter(self, r):
        self.ns.sub = 'list'
        self.ns.filter = 'bar'

        self.add_node('foo')
        self.add_node('bar')

        execute_parser(self.ns)

        assert r.call_count == 1

    @patch.object(Node, 'ping')
    @patch.object(Node, 'repr')
    def test_execute_add_argument(self, r, p):
        address = '123.123.123.123:4567'

        self.ns.sub = 'add'
        self.ns.address = address

        p.return_value = True

        execute_parser(self.ns)

        res = self.session.query(Node).all()
        assert len(res) == 1
        assert res[0].address == address


class TestNodeMessaging(object):
    def setup_method(self, method):
        self.node = Node('thunderboltsandlightning.com')
        self.node.client = MagicMock()

    def test_messaging(self):
        request = {
            'powermetal': True,
        }

        self.node.message(request)

        assert self.node.client.send.called_once_with({
            'paradigm': 'node',
            'address': self.node.address,
            'powermetal': True,
        })
