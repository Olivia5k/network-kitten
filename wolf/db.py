import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_LOCATION = 'sqlite:///data/wolf.db'

# If running tests, use an in memory database
if sys.argv[0].endswith('py.test'):
    DB_LOCATION = 'sqlite://'

# Globals. All tables and queries should use these.
engine = create_engine(DB_LOCATION)
Session = sessionmaker(bind=engine)
Base = declarative_base()
