import os
import re
import logging
import zmq

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

PORT = 5555

logging.basicConfig(level=logging.DEBUG)

engine = create_engine('sqlite:///data/wolf.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)


class WolfServer(object):
    log = logging.getLogger('WolfServer')

    def listen(self, port=PORT):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        host = 'tcp://*:{0}'.format(port)
        socket.bind(host)

        while True:
            self.log.info('Listening on %s', host)
            msg = socket.recv_unicode()
            self.log.info('Got request: %s', msg)
            socket.send_unicode('watup')


class Paradigm(object):
    def scan(self, path):
        roots = []
        has_dir = hasattr(self, 'check_directory')
        has_file = hasattr(self, 'check_file')

        for root, files, dirs in os.walk(path):
            if has_dir:
                for d in dirs:
                    if self.check_directory(d):
                        roots.append(root)
                        break

            if has_file:
                for f in files:
                    if self.check_file(f):
                        roots.append(root)
                        break

        return roots


class ShasumParadigm(Paradigm):
    dir_rxp = re.compile(r'^[0-9a-f]{40}$')
    session = Session()

    def check_directory(self, d):
        name = d.split('/')[-1]

        if self.dir_rxp.search(name):
            return True
        return False

    def load(self):
        return self.session.query(ShasumItem).all()


class ShasumItem(Base):
    __tablename__ = 'shasum'
    id = Column(String(40), primary_key=True)
    files = Column(Text())

    file_rxp = re.compile(r'^[0-9a-f]{40}$')

    log = logging.getLogger('ShasumItem')

    def __init__(self, path):
        self.parsed = False
        self.path = os.path.abspath(path)

    def __repr__(self):
        return '<Shasum {0:.7} [{1}f]>'.format(
            self.id,
            len(self.files.split(','))
        )

    def parse(self):
        if self.parsed:
            return

        self.parsed = True
        self.id = self.path.split('/')[-1]
        self.files = []

        for f in os.listdir(self.path):
            abspath = os.path.join(self.path, f)
            if os.path.isfile(abspath) and self.file_rxp.search(f):
                self.files.append(f)

        self.files = ','.join(self.files)

    def save(self):
        session = Session()

        cls = self.__class__
        res = session.query(cls).filter(cls.id == self.id)
        if res.count():
            self.log.debug('Already in db; skipping')
            return

        self.log.debug('Saving')
        session.add(self)
        session.commit()
        del session

        self.log.debug('Done')

    def serialize(self):
        return {
            'id': self.id,
            'files': self.files,
        }


def main():
    # Base.metadata.create_all(engine)
    WolfServer().listen()


if __name__ == "__main__":
    main()
