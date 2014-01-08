import datetime
import logbook

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from kitten.db import Session
from kitten.db import Base
from kitten.util.names import random_name


class Connection(Base):
    __tablename__ = 'connection'

    id = Column(Integer(), primary_key=True)
    address = Column(String(255))
    port = Column(Integer())
    display_name = Column(String(50))
    created = Column(DateTime, default=datetime.datetime.now)
    last_seen = Column(DateTime, default=datetime.datetime.now)

    log = logbook.Logger('Connection')

    def __init__(self, address, port, display_name=None):
        self.address = address
        self.port = port
        self.display_name = display_name

    def __str__(self):
        return 'Connection<{0.display_name}: {0.address}:{0.port}>'.format(
            self,
        )

    @staticmethod
    def create(address, port, display_name=None):
        session = Session()

        if not display_name:
            display_name = random_name()

        con = Connection(address, port, display_name)
        session.add(con)
        session.commit()
        session.close()

    @staticmethod
    def list():
        session = Session()
        return session.query(Connection).all()


def setup_parser(subparsers):
    con = subparsers.add_parser(
        'connection',
        help="List, add or modify connections."
    )

    sub = con.add_subparsers(help='Connection commands', dest="sub")

    list_ = sub.add_parser('list', help='List connections (default)')

    add = sub.add_parser('add', help='Add a connection')
    add.add_argument('ip', type=str)
    add.add_argument('port', type=int)
    add.add_argument('--display_name', type=str, metavar="<name>")

    remove = sub.add_parser('remove', help='Remove a connection')
    remove.add_argument('name', type=str)

    subparsers.executors.update({
        'connection': execute_parser
    })


def execute_parser(ns):
    if not ns.sub or ns.sub == "list":
        for x, con in enumerate(Connection.list(), start=1):
            print('{0}: {1}'.format(x, con))

    elif ns.sub == 'add':
        Connection.create(ns.ip, ns.port, ns.display_name)
