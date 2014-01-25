import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from kitten import conf

db = conf.DB_URI

# If running tests, use an in memory database
if sys.argv[0].endswith('py.test') or sys.argv == ['setup.py', 'test']:
    db = 'sqlite://'

# Globals. All tables and queries should use these.
engine = create_engine(db)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def setup_core():
    from kitten import node

    node.Node.metadata.bind = engine
    node.Node.metadata.create_all()
