from kitten import db


class MockDatabaseMixin(object):
    def setup_method(self, method):
        db.Base.metadata.create_all(db.engine)
        self.session = db.Session()

    def teardown_method(self, method):
        self.session.close()
        db.Base.metadata.drop_all(db.engine)
