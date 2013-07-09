import unittest
from mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from wolf import connections

engine = create_engine('sqlite:///test/test.db')
connections.Base.metadata.create_all(engine)


class ConnectionTest(unittest.TestCase):
    @patch.object(connections, 'Session')
    def test_create_connection(self, Session):
        Session = sessionmaker(bind=engine)

        connections.Connection.create('test', 'localhost', 65535)

        session = Session()
        res = session.query(connections.Connection).all()
        self.assertEqual(len(res), 1)
