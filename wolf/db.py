from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_LOCATION = '/data/wolf.db'

if False:  # If running tests
    DB_LOCATION = '/test/test.db'

engine = create_engine('sqlite://{0}'.format(DB_LOCATION))
Session = sessionmaker(bind=engine)

Base = declarative_base()
# Base.metadata.create_tables(engine)
