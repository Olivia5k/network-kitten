import json
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

    def __init__(self, request_str):
        self.request_str = request_str
        self._request = None

        self.response = None
        self._response_str = None
        self.exception = None

    def __eq__(self, other):
        return self.request == other.request

    @property
    def request(self):
        """
        Conversion of the request into a Python dictionary.

        Will not raise Exceptions from invalid JSON, but rather store them
        as a state on the request to ease up handling of DB stuffs.

        """

        if not self._request:
            try:
                self._request = json.loads(self.request_str)
            except ValueError:
                self.log.error('Invalid JSON request: {0}', self.request_str)
                self.exception = (
                    RequestError,
                    'INVALID_REQUEST',
                    'Unable to decode JSON request.'
                )
                return None

        return self._request

    def _get_response_string(self):
        """
        String representation of the response.

        No error checking for the JSON is done since we are assuming that the
        input is proper given that it is, y'know, from us.

        If self.response is falsy, None will be returned.

        """

        if not self._response_str:
            if not self.response:
                return None
            self._response_str = json.dumps(self.response)

        return self._response_str

    def _set_response_str(self, item):
        # This is basically to make sure that we can still mock this
        self._response_str = item
        return self._response_str

    response_str = property(_get_response_string, _set_response_str)

    def process(self, socket):
        try:
            response = self.handle()
        except RequestError as e:
            self.log.exception('Request exception')
            response = {
                'code': e.code,
                'message': e.message,
            }
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

        # Dump as JSON string and send it back
        response_str = json.dumps(response)
        socket.send_unicode(response_str)

        # TODO: Handle response

    def handle(self):
        """
        Handle a request.

        This function will take an incoming request, decode it, validate it,
        send it to the appropriate paradigm and handler, get the response,
        validate the response, encode the response and return it back to the
        server.

        Takes a JSON string as input and returns a dictionary.

        """

        self.log.info('Getting new request...')

        self.log.debug('Got request: {0}', self.request)

        # If there was something wrong with the request, the JSON parser in
        # self.request will store the exception so that this can handle it.
        if self.exception:
            exc, params = self.exception[0], self.exception[1:]
            raise exc(*params)

        self.validate_request(self.request)

        paradigm_name = self.request['paradigm']
        method_name = self.request['method'] + '_response'

        paradigm = self.paradigms[paradigm_name]
        method = getattr(paradigm, method_name)

        self.response = method(self.request)

        self.validate_response(self.response)

        self.log.debug('Returning response: {0}', self.response)
        return self.response

    def save(self):
        """
        Commit the request to the database

        """

        kwargs = {
            'sender': "",
            'request': self.request_str,
            'response': self.response_str,
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

    def validate_request(self, request):  # pragma: nocover
        self.log.info('Validating request...')
        self.validator.request(request, self.paradigms)

    def validate_response(self, response):  # pragma: nocover
        self.log.info('Validating response...')
        self.validator.response(response, self.paradigms)
