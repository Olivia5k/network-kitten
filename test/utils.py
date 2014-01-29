from kitten import db
from kitten.client import KittenClient
from kitten.validation import Validator

import mock


class MockDatabaseMixin(object):
    """
    Setup self.session as a SQLalchemy Session and clear tables after each run

    """

    def setup_method(self, method):
        db.Base.metadata.create_all(db.engine)
        self.session = db.Session()

        maybe_super(MockDatabaseMixin, self, 'setup_method', method)

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

        maybe_super(MockKittenClientMixin, self, 'setup_method', method)


class MockValidator(Validator):
    """
    Fake validator that only has one field as okay

    """

    def method_request(self):
        return {'field': {'type': 'number'}}

    def method_response(self):
        return {'code': {'type': 'string'}}


def builtin(target):
    """
    Return the correct string to mock.patch depending on Py3k or not.

    """

    return '{0}.{1}'.format(
        'builtins' if mock.inPy3k else '__builtin__',
        target,
    )


def maybe_super(cls, self, key, *args, **kwargs):
    """
    Call a superclass method, but only if it actually exists.

    This avoids problems when doing multiple inherintance, and is mostly used
    with setup_method of the Mock classes above.

    """

    maybe = getattr(super(cls, self), key, None)
    if maybe:
        maybe(*args, **kwargs)
