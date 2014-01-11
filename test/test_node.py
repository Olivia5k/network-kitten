from kitten import db
from kitten.node import Node


class TestNode(object):
    def setup_method(self, method):
        db.Base.metadata.create_all(db.engine)

    def teardown_method(self, method):
        db.Base.metadata.drop_all(db.engine)

    def test_create_node(self):
        Node.create('localhost', 65535)

        session = db.Session()
        res = session.query(Node).all()

        assert len(res) == 1
        assert res[0].address == "localhost"
        assert res[0].port == 65535

    def test_create_node_with_display_name(self):
        Node.create('localhost', 65535, 'gooby')

        session = db.Session()
        res = session.query(Node).all()

        assert len(res) == 1
        assert res[0].display_name == 'gooby'
