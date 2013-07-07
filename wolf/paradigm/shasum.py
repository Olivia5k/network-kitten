import re
import os
import logging

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from wolf.paradigm.core import Paradigm

engine = create_engine('sqlite:///data/wolf.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)


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

    def ping(self, request):
        self.log.info('Yay ping')
        return {
            'pings': 'fak u dolan'
        }


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
