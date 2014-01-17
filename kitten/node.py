import datetime
import logbook

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from kitten.db import Session
from kitten.db import Base
from kitten.util.ui import TerminalUI
from kitten.util.names import random_name


class Node(Base):
    __tablename__ = 'node'

    id = Column(Integer(), primary_key=True)
    address = Column(String(255))
    display_name = Column(String(50))
    created = Column(DateTime, default=datetime.datetime.now)
    last_seen = Column(DateTime, default=datetime.datetime.now)
    ui = TerminalUI()

    log = logbook.Logger('Node')

    def __init__(self, address, display_name=None):
        self.address = address
        self.display_name = display_name

    def __str__(self):  # pragma: nocover
        return 'Node<{0.display_name}: {0.address}>'.format(self)

    @staticmethod
    def create(address, display_name=None):
        """
        Create a new node

        Try connecting to the node to see if it is eligible for adding.

        """

        if not display_name:
            display_name = random_name()

        con = Node(address, display_name)

        if con.ping():
            session = Session()
            session.add(con)
            session.commit()
            session.close()
            con.ui.success('Created')
        else:
            con.ui.success('Could not connect to node. Node not added.')

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

        request = {'paradigm': 'core'} + data
        response = self.what(request)
        return response

    def ping(self):
        """
        Make a quick ping heartbeat

        Returns boolean success.

        """

        response = self.message({'method': 'ping'})
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
    add.add_argument(
        'display_name',
        type=str,
        metavar="<display_name>",
        nargs="?",
    )

    remove = sub.add_parser('remove', help='Remove a node')
    remove.add_argument('name', type=str)

    subparsers.executors.update({
        'node': execute_parser
    })

    return subparsers


def execute_parser(ns):
    if not ns.sub or ns.sub == "list":
        src = Node.list()

        # If a filter is specified, apply it to the display name
        if hasattr(ns, 'filter') and ns.filter:
            src = list(filter(lambda x: ns.filter in x.display_name, src))

        for con in src:
            print(con.repr())

    elif ns.sub == 'add':
        Node.create(ns.address, ns.display_name)
