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
