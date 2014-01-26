import datetime
import logbook

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from kitten.db import Session
from kitten.db import Base
from kitten.util.ui import TerminalUI
from kitten.client import KittenClient


class Node(Base):
    __tablename__ = 'node'

    id = Column(Integer(), primary_key=True)
    address = Column(String(255))
    created = Column(DateTime, default=datetime.datetime.now)
    last_seen = Column(DateTime, default=datetime.datetime.now)
    ui = TerminalUI()

    client = KittenClient()
    log = logbook.Logger('Node')

    def __init__(self, address):
        self.address = address

    def __str__(self):  # pragma: nocover
        return 'Node<{0.address}>'.format(self)

    @staticmethod
    def create(address):
        """
        Create a new node

        Try connecting to the node to see if it is eligible for adding.

        """

        con = Node(address)

        if con.ping():
            session = Session()
            session.add(con)
            session.commit()
            session.close()
            con.ui.success('Created')
        else:
            con.ui.error('Could not connect to node. Node not added.')

    @staticmethod
    def list():
        """
        Return a list of all nodes

        """

        session = Session()
        return session.query(Node).all()

    def message(self, data):
        """
        Send a message to the node

        """

        request = {
            'paradigm': 'node',
            'address': self.address,
        }
        request.update(data)

        response = self.client.send(request)
        return response

    def ping(self):
        """
        Make a quick ping heartbeat

        Returns boolean success.

        """

        response = self.message({'method': 'ping'})
        return response['success']

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
