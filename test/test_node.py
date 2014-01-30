import pytest
import json

from kitten.conf import DEFAULT_PORT
from kitten.node import Node
from kitten.node import NodeParadigm
from kitten.node import NodeValidator
from kitten.node import setup_parser
from kitten.node import execute_parser
from test.utils import MockDatabaseMixin
from test.utils import MockKittenClientMixin

from mock import MagicMock, patch, call

from kitten.server import RequestError
from jsonschema.exceptions import ValidationError


class NodeTestBase(MockDatabaseMixin):
    def setup_method(self, method):
        self.patch_classes(Node)
        super(NodeTestBase, self).setup_method(method)

    def add_node(self, address):
        node = Node(address)
        self.session.add(node)
        self.session.commit()


class TestNodeCreation(NodeTestBase):
    def setup_method(self, method):
        self.address = 'localhost:63161'
        super(TestNodeCreation, self).setup_method(method)

    @patch.object(Node, 'ping')
    def test_create_node(self, p):
        p.return_value = True
        Node.create(self.address)

        res = self.session.query(Node).all()

        assert len(res) == 1
        assert res[0].address == self.address

    @patch.object(Node, 'ping')
    def test_create_node_without_port_gets_default_port(self, p):
        p.return_value = True
        Node.create('localhost')

        res = self.session.query(Node).all()

        assert len(res) == 1
        assert res[0].address == "localhost:{0}".format(DEFAULT_PORT)

    @patch.object(Node, 'ping')
    def test_create_node_ping_fails(self, p):
        p.return_value = False
        Node.create(self.address)

        res = self.session.query(Node).all()

        assert len(res) == 0

    @patch.object(Node, 'ping')
    def test_create_node_already_exists(self, p):
        address = self.address

        self.add_node(address)
        Node.create(address)

        res = self.session.query(Node).all()
        assert len(res) == 1


class TestNodeArgparser(object):
    def setup_method(self, method):
        self.subparsers = MagicMock()

    def test_setup_parser_sets_up_node_namespace(self):
        setup_parser(self.subparsers)
        assert self.subparsers.add_parser.call_args[0][0] == 'node'

    def test_setup_parser_sets_up_executor(self):
        ret = setup_parser(self.subparsers)
        assert ret is execute_parser


class TestNodeArgparserIntegration(NodeTestBase):
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

    @patch.object(Node, 'paradigm')
    @patch.object(Node, 'ping')
    @patch.object(Node, 'repr')
    def test_execute_add_argument(self, r, p, paradigm):
        address = '123.123.123.123:4567'

        self.ns.sub = 'add'
        self.ns.address = address

        p.return_value = True

        execute_parser(self.ns)

        res = self.session.query(Node).all()
        assert len(res) == 1
        assert res[0].address == address
        assert paradigm.send.called


class TestNodeMessaging(object):
    def setup_method(self, method):
        self.node = Node('thunderboltsandlightning.com')
        self.node.paradigm = MagicMock()

    def test_messaging_adds_address(self):
        request = {}
        self.node.message(request)

        self.node.paradigm.send.assert_called_once_with(
            self.node.address,
            request,
        )


class TestNodeMessagingIntegration(MockKittenClientMixin):
    def setup_method(self, method):
        self.host = 'tesseract.localnet:61214'
        self.node = Node(self.host)
        super(TestNodeMessagingIntegration, self).setup_method(method)

    @patch('zmq.Poller')
    @patch('zmq.Context')
    def test_ping(self, ctx, poller):
        ctx.return_value = self.context

        j = '{"pong": true, "method": "ping", "paradigm": "node"}'
        self.socket.recv_unicode.return_value = j
        poller.return_value.poll.return_value = [(self.socket, 1)]

        ret = self.node.ping()

        assert ret is True
        assert self.socket.send_unicode.called

        # Make sure that it adds the tcp:// part.
        self.socket.connect.assert_called_once_with(
            'tcp://{0}'.format(self.host),
        )

    @patch.object(Node, 'message')
    def test_ping_keyerror(self, message):
        message.side_effect = KeyError
        ret = self.node.ping()

        assert ret is False

    @patch.object(Node, 'message')
    def test_ping_requesterror(self, message):
        message.side_effect = RequestError('code', 'msg')
        ret = self.node.ping()

        assert ret is False

    @patch.object(Node, 'message')
    def test_ping_validationerror(self, message):
        message.side_effect = ValidationError('msg')
        ret = self.node.ping()

        assert ret is False


class TestNodeParadigmPing(object):
    def setup_method(self, method):
        self.paradigm = NodeParadigm()

    def test_ping_response(self):
        ret = self.paradigm.ping_response({})
        assert ret == {
            'pong': True,
            'method': 'ping',
            'paradigm': 'node',
        }


class TestNodeValidator(object):
    def setup_method(self, method):
        self.paradigms = {
            'node': NodeParadigm(),
        }

        self.validator = NodeValidator()
        self.request = {
            'paradigm': 'node',
            'method': 'ping',
        }

    def test_ping_request(self):
        self.validator.request(self.request, self.paradigms)

    def test_ping_request_extra_field(self):
        self.request['hehe'] = True
        with pytest.raises(ValidationError):
            self.validator.request(self.request, self.paradigms)


class TestNodeSync(NodeTestBase, MockKittenClientMixin):
    def setup_method(self, method):
        self.node = Node('lament.toy.factory.com:1234')
        super(TestNodeSync, self).setup_method(method)

    @patch.object(Node, 'create')
    @patch('zmq.Poller')
    @patch('zmq.Context')
    def test_sync_no_new_nodes(self, ctx, poller, create):
        ctx.return_value = self.context

        self.socket.recv_unicode.return_value = json.dumps({
            'method': 'sync',
            'paradigm': 'node',
            'nodes': [],
        })
        poller.return_value.poll.return_value = [(self.socket, 1)]

        self.node.sync()

        self.socket.send_unicode.assert_called_once_with(
            json.dumps({
                'method': 'sync',
                'paradigm': 'node',
                'nodes': [],
            })
        )
        assert not create.called

    @patch.object(Node, 'create')
    @patch('zmq.Poller')
    @patch('zmq.Context')
    def test_sync_new_nodes(self, ctx, poller, create):
        ctx.return_value = self.context
        node = 'node.js'

        self.socket.recv_unicode.return_value = json.dumps({
            'method': 'sync',
            'paradigm': 'node',
            'nodes': [node],
        })
        poller.return_value.poll.return_value = [(self.socket, 1)]

        self.node.sync()

        self.socket.send_unicode.assert_called_once_with(
            json.dumps({
                'nodes': [],
                'method': 'sync',
                'paradigm': 'node',
            })
        )

        create.assert_called_once_with(node, False)

    @patch.object(Node, 'create')
    @patch('zmq.Poller')
    @patch('zmq.Context')
    def test_sync_multiple_new_nodes(self, ctx, poller, create):
        ctx.return_value = self.context
        nodes = ['neverland.ca.org', 'node.js', 'hehe.people.nu']

        self.socket.recv_unicode.return_value = json.dumps({
            'method': 'sync',
            'paradigm': 'node',
            'nodes': nodes,
        })
        poller.return_value.poll.return_value = [(self.socket, 1)]

        self.node.sync()

        self.socket.send_unicode.assert_called_once_with(
            json.dumps({
                'nodes': [],
                'method': 'sync',
                'paradigm': 'node',
            })
        )

        calls = create.call_args_list
        assert len(calls) == 3
        for x, address in enumerate(nodes):
            assert calls[x] == call(address, False)

    def test_sync_response(self):
        nodes = ['neverland.ca.org', 'node.js', 'hehe.people.nu']
        for address in nodes:
            self.add_node(address)

        ret = self.node.paradigm.sync_response({'nodes': []})
        assert ret == {
            'nodes': nodes,
            'method': 'sync',
            'paradigm': 'node',
        }

    def test_sync_response_already_has_one(self):
        nodes = ['neverland.ca.org', 'node.js', 'hehe.people.nu']
        for address in nodes:
            self.add_node(address)

        ret = self.node.paradigm.sync_response({'nodes': ['node.js']})

        assert 'node.js' not in ret['nodes']
