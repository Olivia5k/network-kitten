import json
import logging
import zmq
import jsonschema

from wolf.paradigm.shasum import ShasumParadigm
from wolf.validation import validate

PORT = 5555
logging.basicConfig(level=logging.DEBUG)


class RequestException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return "{0}: {1}".format(self.code, self.message)


class WolfServer(object):
    log = logging.getLogger('WolfServer')

    def __init__(self):
        self.paradigms = {}

    def listen_forever(self, port=PORT):  # pragma: nocover
        context = zmq.Context()
        socket = context.socket(zmq.REP)

        host = 'tcp://*:{0}'.format(port)
        socket.bind(host)
        self.log.info('Listening on %s', host)

        while True:
            request_str = socket.recv_unicode()

            try:
                response = self.handle_request(request_str)
            except RequestException as e:
                response = {
                    'code': e.code,
                    'message': e.message,
                }
            except jsonschema.exceptions.ValidationError as e:
                response = {
                    'code': 'VALIDATION_ERROR',
                    'message': e.message,
                }
            except Exception as e:
                self.log.exception('Request handling exception')
                response = {
                    'code': 'UNKNOWN_ERROR',
                    'message': e.value,
                }

            response_str = json.dumps(response)
            socket.send_unicode(response_str)

            # Separate blocks per request, for now
            print()

    def setup(self):
        self.log.info('Setting up server')
        self.paradigms = self.get_paradigms()

        # TODO: Create database tables

    def get_paradigms(self, *paradigms):
        self.log.info('Loading paradigms')
        return {
            'shasum': ShasumParadigm()
        }

    def validate_request(self, request):
        self.log.info('Validating request...')
        validate(request, 'core')

    def validate_response(self, response):
        self.log.info('Validating response...')

    def handle_request(self, request_str):
        """
        Handle a request.

        This is the meat of the server. This function will take an incoming
        request, decode it, validate it, send it to the appropriate paradigm
        and handler, get the response, validate the response, encode the
        response and return it back to the server.

        Takes a JSON string as input and returns a dictionary.

        """

        self.log.info('Getting new request...')

        try:
            request = json.loads(request_str)
        except ValueError:
            self.log.error('Invalid JSON request: %s', request_str)
            raise RequestException(
                'INVALID_REQUEST',
                'Unable to decode JSON request.'
            )

        self.log.debug('Got request: %s', request)

        self.validate_request(request)

        paradigm_name = request['paradigm']
        method_name = request['method']

        paradigm = self.paradigms[paradigm_name]
        method = getattr(paradigm, method_name, None)

        response = method(request)

        self.validate_response(response)

        self.log.debug('Returning response: %s', response)
        return response


def main():  # pragma: nocover
    logging.info('Starting wolf server')
    server = WolfServer()
    server.setup()

    server.listen_forever()

if __name__ == "__main__":  # pragma: nocover
    main()
