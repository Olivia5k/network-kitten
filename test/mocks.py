from kitten import db
from kitten.client import KittenClient
from kitten.validation import Validator
from kitten.paradigm import Paradigm
from kitten.paradigm import annotate

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from test.utils import maybe_super

import mock


class MockDatabaseMixin(object):
    """
    Setup an in-memory database, db helpers and complete clear after each run

    Use this as a superclass whenever a test touches the database. See
    test.test_node.NodeTestBase for an example on how to implement this.

    """

    engine = create_engine('sqlite://')
    Session = sessionmaker(bind=engine)
    Base = declarative_base()

    def setup_method(self, method):
        self.Base.metadata.create_all(self.engine)
        self.session = self.Session()

        maybe_super(MockDatabaseMixin, self, 'setup_method', method)

    def teardown_method(self, method):
        self.session.close()
        self.Base.metadata.drop_all(self.engine)

    # It might be that this class could be faster if it did not do this always.
    def patch_classes(self, *classes):
        engine = create_engine('sqlite://')

        db.Session.configure(bind=engine)
        self.Session.configure(bind=engine)

        for cls in classes:
            cls.metadata.bind = engine
            cls.metadata.create_all()


class MockKittenClientMixin(object):
    """
    Used whenever you need to patch the inner parts of the KittenClient but not
    the entire class or call.

    Methods that use this need to @mock.patch('zmq.green.Context') and assign
    the return_value of that mock to be self.context.

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


class MockParadigm(Paradigm):
    validator = MockValidator()

    @annotate
    def method_request(self, request):
        return {
            'code': 'OK'
        }

    @annotate
    def method_response(self, request):
        return {
            'code': 'OK'
        }
