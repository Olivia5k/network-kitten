from kitten import db

from mock import MagicMock, patch


class TestDatabase(object):
    def setup_method(self, method):
        self.ns = MagicMock()

    @patch('kitten.db.Session')
    @patch('kitten.db.create_engine')
    def test_setup_core(self, ce, session):
        self.ns.port = 9011
        db.setup_core(self.ns)

        assert 'kitten-9011.db' in ce.call_args_list[0][0][0]

    @patch('kitten.db.Session')
    @patch('kitten.db.create_engine')
    def test_setup_core_different_port(self, ce, session):
        self.ns.port = 57757
        db.setup_core(self.ns)

        assert 'kitten-57757.db' in ce.call_args_list[0][0][0]

    @patch('kitten.db.Session')
    @patch('kitten.db.create_engine')
    def test_setup_core_create_self(self, ce, session):
        session.return_value.query.return_value.scalar.return_value = False
        self.ns.port = 57757
        db.setup_core(self.ns)

        assert session.return_value.add.call_count == 1
