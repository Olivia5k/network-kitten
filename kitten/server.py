import os
import json
import signal
import zmq
import jsonschema
import logbook

from kitten import conf
from kitten.validation import Validator
import kitten.node


class RequestError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):  # pragma: nocover
        return "{0}: {1}".format(self.code, self.message)


class KittenServer(object):
    log = logbook.Logger('KittenServer')
    torn = False

    def __init__(self, validator):
        self.paradigms = {}
        self.validator = validator

    def listen_forever(self, port=conf.PORT):  # pragma: nocover
        """
        Listen on the socket forever

        This is pragma: nocover since it is by definition an infinite loop. All
        the related units have their own tests.

        """

        try:
            socket = self.get_socket(port)

            # As long as listen returns positive, listen forever.
            while self.listen(socket):
                pass

        except Exception:
            # TODO: Move into the loop
            self.log.exception('Server died.')

        finally:
            # This usually means that the server died.
            self.teardown()

    def listen(self, socket):
        try:
            # Listen on the socket; the actual wait is here
            request_str = socket.recv_unicode()
        except zmq.error.ZMQError as e:
            # This is for graceful exit of the socket
            self.log.info('Socket interrupted')
            return False

        try:
            # Send the request for processing and handle any errors
            response = self.handle_request(request_str)
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

        # Return True to keep the listen_forever loop going
        return True

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
            self.log.error('Invalid JSON request: {0}', request_str)
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

    def setup(self):
        self.log.info('Setting up server')
        self.paradigms = self.get_paradigms()
        self.setup_signals()
        self.setup_pidfile()

    def setup_signals(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_pidfile(self):
        pid = str(os.getpid())
        self.log.debug('Pid: {0}', pid)
        with open(conf.PIDFILE, 'w') as pidfile:
            pidfile.write(pid)

    def signal_handler(self, signum, frame):
        names = {2: 'SIGINT', 15: 'SIGTERM'}
        self.log.warning('Recieved {0}', names[signum])
        self.teardown()

    def teardown(self):
        if self.torn:
            return

        self.torn = True
        self.log.info('Tearing down server')
        self.teardown_pidfile()

    def teardown_pidfile(self):
        self.log.debug('Removing pidfile')
        os.remove(conf.PIDFILE)

    def get_socket(self, port):
        context = zmq.Context()
        socket = context.socket(zmq.REP)

        host = 'tcp://*:{0}'.format(port)
        socket.bind(host)
        self.log.info('Listening on {0}', host)

        return socket

    def get_paradigms(self):  # pragma: nocover
        self.log.info('Loading paradigms')
        return {
            'node': kitten.node.NodeParadigm(),
        }

    def validate_request(self, request):
        self.log.info('Validating request...')
        self.validator.request(request, self.paradigms)

    def validate_response(self, response):
        self.log.info('Validating response...')
        self.validator.response(response, self.paradigms)


def setup_parser(subparsers):
    server = subparsers.add_parser(
        'server',
        help="Start or stop the server"
    )

    sub = server.add_subparsers(help='Server commands', dest="server_command")
    start = sub.add_parser('start', help='Start the server (default)')
    stop = sub.add_parser('stop', help='Stop the server')

    for p in (server, start, stop):
        p.add_argument(
            '--port',
            type=int,
            default=conf.DEFAULT_PORT,
            metavar='<port>',
            help='Port to listen on, default {0}'.format(conf.DEFAULT_PORT),
        )

    return execute_parser


def execute_parser(ns):
    # TODO: Test that specifying a port actually leads to it being used
    port = ns.port if ns.port else conf.PORT

    if ns.server_command == "stop":
        return stop_server(port)
    else:
        start_server(port)


def is_running():
    # Use existence of the pidfile to determine if the server is running
    return os.path.isfile(conf.PIDFILE)


def start_server(port):
    logbook.info('Starting kitten server')

    validator = Validator()
    server = KittenServer(validator)
    server.setup()

    server.listen_forever(port)


def stop_server(port):
    if not os.path.exists(conf.PIDFILE):
        logbook.error(
            'No pidfile found; kitten server is probably not running',
        )
        return 1

    logbook.info('Stopping kitten server')
    # Send sigint to PIDFILE and let the server gracefully tear down.
    with open(conf.PIDFILE) as f:
        pid = int(f.read())
        os.kill(pid, signal.SIGINT)

    return 0
