from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from kitten import conf

Base = declarative_base()
Session = sessionmaker()


def setup_core(ns):
    db = 'sqlite:///{0}/kitten-{1}.db'.format(conf.DATA_DIR, ns.port)
    engine = create_engine(db)
    Session.configure(bind=engine)

    from kitten import node
    node.Node.metadata.bind = engine
    node.Node.metadata.create_all()
