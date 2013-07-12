import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from wolf import conf

db = conf.DB_URI

# If running tests, use an in memory database
if sys.argv[0].endswith('py.test'):
    db = 'sqlite://'

# Globals. All tables and queries should use these.
engine = create_engine(db)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def setup_core():
    from wolf import connections

    connections.Connection.metadata.bind = engine
    connections.Connection.metadata.create_all()
