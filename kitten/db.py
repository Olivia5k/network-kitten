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

    # XXX: This is... no.
    from kitten import request
    request.KittenRequestItem.metadata.bind = engine
    request.KittenRequestItem.metadata.create_all()

    address = '{0}:{1}'.format(conf.ADDRESS, ns.port)

    session = Session()
    q = session.query(node.Node).filter(node.Node.address == address)

    if not session.query(q.exists()).scalar():
        session.add(node.Node(address))
        session.commit()

    session.close()
