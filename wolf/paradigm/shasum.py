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

from wolf import conf
from wolf.db import Base
from wolf.db import Session
from wolf.db import engine
from wolf.util import mkdir
from wolf.paradigm.core import Paradigm

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

    id = Column(String(40), primary_key=True)
    owner = Column(Integer, ForeignKey('connection.id'), default=0)
    files = Column(Text)
    created = Column(DateTime, default=datetime.datetime.now)

    file_rxp = re.compile(r'^[0-9a-f]{40}$')

    log = logbook.Logger('ShasumItem')

    def __init__(self, id, files, owner=0, created=None):
        self.id = id
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

        files = [f for f in os.listdir(path)]
        files = ','.join(files)

        shasum = ShasumItem(id, files)
        shasum.save()
        return shasum

    def save(self):
        session = Session()

        cls = self.__class__
        res = session.query(cls).filter(cls.id == self.id)
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
