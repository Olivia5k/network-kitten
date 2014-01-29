import re
import datetime
import logbook

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

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


class NodeParadigm(Paradigm):
    validator = NodeValidator()

    def setup(self):  # pragma: nocover
        pass

    @annotate
    def ping_request(self, request):
        return {}

    @annotate
    def ping_response(self, request):
        return {
            'pong': True
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

    @staticmethod
    def create(address):
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
        """
        Send a message to the node

        """

        self.paradigm.validator.request(request, {'node': self.paradigm})
        response = self.paradigm.client.send(self.address, request)
        self.paradigm.validator.response(response, {'node': self.paradigm})

        return response

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

    def repr(self):  # pragma: nocover
        return self.__str__()


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
        Node.create(ns.address)
