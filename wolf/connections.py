import logging

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from wolf.db import Session
from wolf.db import Base
from wolf.util.names import random_name


class Connection(Base):
    __tablename__ = 'connection'
    id = Column(Integer(), primary_key=True)
    address = Column(String(255))
    port = Column(Integer())
    display_name = Column(String(50))

    log = logging.getLogger('Connection')

    def __init__(self, address, port, display_name=None):
        self.address = address
        self.port = port
        self.display_name = display_name

    @staticmethod
    def create(address, port, display_name=None):
        session = Session()

        if not display_name:
            display_name = random_name()

        con = Connection(address, port, display_name)
        session.add(con)
        session.commit()
        session.close()


def setup_parser(subparsers):
    con = subparsers.add_parser(
        'connection',
        help="List, add or modify connections."
    )

    sub = con.add_subparsers(help='Sub-commands', dest="sub")

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
    pass
