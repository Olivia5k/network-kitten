import re
import datetime
import logbook

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql.expression import not_

from kitten import conf
from kitten.db import Session
from kitten.db import Base
from kitten.paradigm import Paradigm
from kitten.paradigm import annotate
from kitten.server import RequestError
from kitten.validation import Validator
from jsonschema.exceptions import ValidationError


class NodeValidator(Validator):
    def ping_request(self):
        return {}

    def ping_response(self):
        return {
            'pong': {
                'type': 'boolean'
            }
        }

    def sync_request(self):
        return {
            'nodes': {
                'type': 'array',
                'items': {
                    'type': 'string',
                },
            }
        }

    def sync_response(self):
        return {
            'nodes': {
                'type': 'array',
                'items': {
                    'type': 'string',
                },
            }
        }


class NodeParadigm(Paradigm):
    validator = NodeValidator()

    @annotate
    def ping_request(self, request):
        return {}

    @annotate
    def ping_response(self, request):
        return {
            'pong': True
        }

    @annotate
    def sync_request(self, request):
        return request

    @annotate
    def sync_response(self, request):
        """
        Process a request to sync

        Return all nodes present in local database but not provided in request,
        and create new nodes for all nodes present in request but not in local
        database.

        """

        session = Session()

        nodes = set(request['nodes'])
        own = set(n.address for n in session.query(Node).all())

        to_requester = list(own - nodes)
        to_me = list(nodes - own)

        # This should be in a greenlet
        for address in to_me:
            Node.create(address, True)

        session.close()
        return {
            'nodes': sorted(to_requester),
        }


class Node(Base):
    __tablename__ = 'node'
    paradigm = NodeParadigm()

    id = Column(Integer(), primary_key=True)
    address = Column(String(255))
    created = Column(DateTime, default=datetime.datetime.now)
    last_seen = Column(DateTime, default=datetime.datetime.now)

    log = logbook.Logger('Node')

    def __init__(self, address):
        self.address = address

    def __str__(self):  # pragma: nocover
        return '<Node: {0.address}>'.format(self)

    def repr(self):  # pragma: nocover
        return self.__str__()

    @staticmethod
    def create(address, sync=False):
        """
        Create a new node

        Try connecting to the node to see if it is eligible for adding.

        """

        session = Session()

        # If no port is specified, make sure to add the default.
        if not re.search(r':\d+', address):
            address += ':{0}'.format(conf.DEFAULT_PORT)

        con = Node(address)
        q = session.query(Node).filter(Node.address == address)

        if session.query(q.exists()).scalar():
            con.log.error('{0} already exists.'.format(con))
            return

        if con.ping():
            session.add(con)
            session.commit()
            con.log.info('{0} added.'.format(con))

            if sync:
                con.sync()
        else:
            con.log.error('Could not connect to {0}.'.format(con))

        session.close()

    @staticmethod
    def list():
        """
        Return a list of all nodes

        """

        session = Session()
        return session.query(Node).all()

    def message(self, request):
        return self.paradigm.send(self.address, request)

    def ping(self):
        """
        Send a quick ping heartbeat to the node

        Returns boolean success.

        """

        try:
            request = self.paradigm.ping_request({})
            response = self.message(request)
            return response['pong']

        except (KeyError, RequestError, ValidationError):
            self.log.exception('Ping failed')
            return False

    def sync(self):
        """
        Sync the node list with another node

        """

        nodes = [n.address for n in Node.list()]
        request = self.paradigm.sync_request({
            'nodes': nodes,
        })

        response = self.message(request)

        for address in response['nodes']:
            Node.create(address, False)


def setup_parser(subparsers):
    con = subparsers.add_parser('node', help="List, add or modify nodes.")
    sub = con.add_subparsers(help='Node commands', dest="sub")

    list_ = sub.add_parser('list', help='List nodes (default)')
    list_.add_argument('--filter', type=str)

    add = sub.add_parser('add', help='Add a node')
    add.add_argument('address', type=str)

    remove = sub.add_parser('remove', help='Remove a node')
    remove.add_argument('name', type=str)

    return execute_parser


def execute_parser(ns):
    if not ns.sub or ns.sub == "list":
        src = Node.list()

        # If a filter is specified, apply it to the display name
        if hasattr(ns, 'filter') and ns.filter:
            src = list(filter(lambda x: ns.filter in x.address, src))

        for con in src:
            print(con.repr())

    elif ns.sub == 'add':
        Node.create(ns.address, True)
