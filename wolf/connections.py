import logging

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from wolf.util.names import random_name

engine = create_engine('sqlite:///data/wolf.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Connection(Base):
    __tablename__ = 'connection'
    id = Column(Integer(), primary_key=True)
    address = Column(String(255))
    port = Column(Integer())
    display_name = Column(String(50))

    log = logging.getLogger('Connection')

    def __init__(self, id, address, port, display_name=None):
        self.id = id
        self.address = address
        self.port = port
        self.display_name = display_name

    @staticmethod
    def connect(id):
        return

    @staticmethod
    def create(id_, address, port, display_name=None):
        session = Session()
        if display_name is None:
            display_name = random_name()

        con = Connection(id_, address, port, display_name)
        session.add(con)
        session.commit()

        session.close()
        del session
