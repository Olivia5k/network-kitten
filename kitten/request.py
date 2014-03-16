import jsonschema
import logbook
import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from kitten.db import Base
from kitten.db import Session
from kitten.util import AutoParadigmMixin
from kitten.validation import Validator


class RequestError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):  # pragma: nocover
        return "{0}: {1}".format(self.code, self.message)


class KittenRequestItem(Base):
    __tablename__ = 'request'

    id = Column(Integer(), primary_key=True)
    sender = Column(String(255))
    request = Column(Text())
    response = Column(Text())
    created = Column(DateTime, default=datetime.datetime.now)


class KittenRequest(AutoParadigmMixin):
    log = logbook.Logger('KittenRequest')
    validator = Validator()

    def __init__(self, request):
        self.request = request
        self.response = None

    def __eq__(self, other):
        return self.request == other.request

    @property
    def host(self):
        kind = self.request['id']['kind']

        if kind == 'request':
            key = 'to'
        elif kind == 'response':
            key = 'from'

        return 'tcp://{0}'.format(self.request['id'][key])

    def process(self, socket):
        try:
            response = self.process_request()
        except jsonschema.exceptions.ValidationError as e:
            self.log.exception('Validation error')
            response = {
                'code': 'VALIDATION_ERROR',
                'message': e.message,
            }
        except Exception as e:
            self.log.exception('General exception')
            response = {
                'code': 'UNKNOWN_ERROR',
                'message': str(e),
            }

        # Send it back!
        response = self.decorate_response(response)
        socket.send_json(response)

        # Wait for confirmation
        confirm = socket.recv_json()
        self.process_confirm(confirm)

    def process_request(self):
        """
        Process the request.

        This function will take an incoming request, decode it,
        send it to the appropriate paradigm and handler, get the response,
        validate the response, and return it.

        """

        self.log.info('Got request: {0}', self.request)

        self.validate_request(self.request)

        paradigm_name = self.request['paradigm']
        method_name = self.request['method'] + '_response'

        paradigm = self.paradigms[paradigm_name]
        method = getattr(paradigm, method_name)

        self.response = method(self.request)
        self.validate_response(self.response)

        self.log.debug('Returning response: {0}', self.response)
        return self.response

    def process_confirm(self, response):
        """
        Process the confirmation for the request

        """

        # TODO: Error handling? Committing to db?
        pass

    def save(self):
        """
        Commit the request to the database

        """

        kwargs = {
            'sender': "",
            'request': self.request,
            'response': self.response,
        }

        session = Session()
        item = KittenRequestItem(**kwargs)

        session.add(item)
        session.commit()
        session.close()

    def ack(self):
        return {
            'ack': True
        }

    def decorate_response(self, response):
        response.update({
            'id': self.request['id'],
            'paradigm': self.request['paradigm'],
            'method': self.request['method'],
        })

        return response

    def validate_request(self, request):  # pragma: nocover
        self.log.info('Validating request...')
        self.validator.request(request, self.paradigms)

    def validate_response(self, response):  # pragma: nocover
        self.log.info('Validating response...')
        self.validator.response(response, self.paradigms)
