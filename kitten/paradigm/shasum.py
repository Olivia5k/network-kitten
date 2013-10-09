import re
import os
import datetime
import logbook

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from kitten import conf
from kitten.db import Base
from kitten.db import Session
from kitten.db import engine
from kitten.util import mkdir
from kitten.paradigm.core import Paradigm

TEMP_BASE = os.path.join(conf.CACHE_DIR, 'shasum')


class ShasumParadigm(Paradigm):
    dir_rxp = re.compile(r'^[0-9a-f]{40}$')
    session = Session()

    def setup(self):
        self.log.info('Setting up ShasumParadigm')

        self.log.debug('Creating tables')
        ShasumItem.metadata.bind = engine
        ShasumItem.metadata.create_all()

        mkdir(TEMP_BASE)

        for root in self.scan(TEMP_BASE):
            for path in os.listdir(root):
                ShasumItem.create(os.path.join(root, path))

    def check_directory(self, path):
        name = path.split('/')[-1]

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    sha = Column(String(40))
    owner = Column(Integer, ForeignKey('connection.id'), default=0)
    files = Column(Text)
    created = Column(DateTime, default=datetime.datetime.now)

    file_rxp = re.compile(r'^[0-9a-f]{40}$')

    log = logbook.Logger('ShasumItem')

    def __init__(self, sha, files, owner=0, created=None):
        self.sha = sha
        self.owner = owner
        self.files = files

        if created:
            self.created = created

    def __repr__(self):
        return '<Shasum {0:.7} [{1}]>'.format(self.id, self.files)

    @staticmethod
    def create(path):
        id = path.split('/')[-1]
        ShasumItem.log.debug('Create: {0}', id)

        path = os.path.abspath(path)
        files = ','.join(f for f in os.listdir(path))

        shasum = ShasumItem(id, files)
        shasum.save()
        return shasum

    def save(self):
        session = Session()

        cls = self.__class__
        res = session.query(cls).filter(cls.sha == self.sha)
        if res.count():
            self.log.debug('{0}: Already in db; skipping', self)
            return

        self.log.debug('{0}: Saving', self)
        session.add(self)
        session.commit()
        del session

    def serialize(self):
        return {
            'id': self.id,
            'files': self.files,
        }
