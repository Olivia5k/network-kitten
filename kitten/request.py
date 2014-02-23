import json
import jsonschema
import logbook

import kitten.validation
from kitten.util import AutoParadigmMixin


class RequestError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):  # pragma: nocover
        return "{0}: {1}".format(self.code, self.message)


class KittenRequest(AutoParadigmMixin):
    log = logbook.Logger('KittenRequest')
    validator = kitten.validation.Validator()

    def __init__(self, request_str):
        self.request_str = request_str

    def process(self, socket):
        try:
            response = self.handle_request()
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

        try:
            request = json.loads(self.request_str)
        except ValueError:
            self.log.error('Invalid JSON request: {0}', self.request_str)
            raise RequestError(
                'INVALID_REQUEST',
                'Unable to decode JSON request.'
            )

        self.log.debug('Got request: {0}', request)

        self.validate_request(request)

        paradigm_name = request['paradigm']
        method_name = request['method'] + '_response'

        paradigm = self.paradigms[paradigm_name]
        method = getattr(paradigm, method_name, None)

        response = method(request)

        self.validate_response(response)

        self.log.debug('Returning response: {0}', response)
        return response

    def ack(self):
        return {'ack': True}

    def validate_request(self, request):
        self.log.info('Validating request...')
        self.validator.request(request, self.paradigms)

    def validate_response(self, response):
        self.log.info('Validating response...')
        self.validator.response(response, self.paradigms)
