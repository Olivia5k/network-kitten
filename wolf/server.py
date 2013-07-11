import os
import json
import logging
import signal
import zmq
import jsonschema

from wolf import conf
from wolf.paradigm.shasum import ShasumParadigm
from wolf.validation import validate


class RequestException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return "{0}: {1}".format(self.code, self.message)


class WolfServer(object):
    log = logging.getLogger('WolfServer')
    torn = False

    def __init__(self):
        self.paradigms = {}

    def listen_forever(self, port=conf.PORT):  # pragma: nocover
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REP)

            host = 'tcp://*:{0}'.format(port)
            socket.bind(host)
            self.log.info('Listening on %s', host)

            while True:
                try:
                    request_str = socket.recv_unicode()
                except zmq.error.ZMQError as e:
                    # This is for graceful exit of the socket
                    self.log.info('Socket interrupted')
                    return

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

        finally:
            # This usually means that the server died.
            self.teardown()

    def setup(self):
        self.log.info('Setting up server')
        self.paradigms = self.get_paradigms()

        # Set up signal handlers
        def handle(signum, frame):
            names = {2: 'SIGINT', 15: 'SIGTERM'}
            self.log.warning('Recieved %s', names[signum])
            self.teardown()

        signal.signal(signal.SIGINT, handle)
        signal.signal(signal.SIGTERM, handle)

        # Set up pidfile
        pid = str(os.getpid())
        self.log.debug('Running on pid %s', pid)
        with open(conf.PIDFILE, 'w') as pidfile:
            pidfile.write(pid)

    def teardown(self):
        if self.torn:
            return

        self.torn = True
        self.log.info('Tearing down server')

        self.log.debug('Removing pidfile')
        os.remove(conf.PIDFILE)

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


def setup_parser(subparsers):
    server = subparsers.add_parser(
        'server',
        help="Start or stop the server"
    )

    sub = server.add_subparsers(help='Server commands', dest="server_command")
    sub.add_parser('start', help='Start the server (default)')
    sub.add_parser('stop', help='Stop the server')

    subparsers.executors.update({
        'server': execute_parser
    })


def execute_parser(ns):
    if ns.server_command == "stop":
        stop_server()
        return 0
    else:
        start_server()


def is_running():
    # Use existance of the pidfile to determine if the server is running
    return os.path.isfile(conf.PIDFILE)


def start_server():
    logging.info('Starting wolf server')
    server = WolfServer()
    server.setup()

    server.listen_forever()


def stop_server():
    logging.info('Stopping wolf server')
    # Send sigint to PIDFILE and let the server gracefully tear down.
    pid = int(open(conf.PIDFILE).read())
    os.kill(pid, signal.SIGINT)
