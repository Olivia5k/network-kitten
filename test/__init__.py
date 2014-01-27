from kitten import db
from kitten.client import KittenClient

import mock


class MockDatabaseMixin(object):
    def setup_method(self, method):
        db.Base.metadata.create_all(db.engine)
        self.session = db.Session()

    def teardown_method(self, method):
        self.session.close()
        db.Base.metadata.drop_all(db.engine)


class MockKittenClientMixin(object):
    """
    Used whenever you need to patch the inner parts of the KittenClient but not
    the entire class or call.

    Methods that use this need to @mock.patch('zmq.Context') and assign the
    return_value of that mock to be self.context.

    """

    def setup_method(self, method):
        self.client = KittenClient()
        self.context = mock.MagicMock()
        self.socket = mock.MagicMock()
        self.context.socket.return_value = self.socket
