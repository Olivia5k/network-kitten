import os
import json
import signal
import zmq.green as zmq
import logbook

import gevent
import gevent.pool
from gevent.queue import Queue

from kitten import conf
import kitten.validation
import kitten.node
from kitten.request import KittenRequest


class KittenServer(object):
    log = logbook.Logger('KittenServer')
    torn = False

    def __init__(self, ns, validator):
        self.ns = ns
        self.validator = validator
        self.pool = gevent.pool.Pool(5)
        self.queue = Queue()

    def listen(self, socket):
        request_str = socket.recv_unicode()
        # Send the request for processing and handle any errors
        response = self.handle_request(request_str)

        # Dump as JSON string and send it back
        response_str = json.dumps(response)
        socket.send_unicode(response_str)

    def listen_forever(self):  # pragma: nocover
        try:
            socket = self.get_socket()
            while not self.torn:
                self.listen(socket)

        finally:
            self.log.exception('Server died.')
            self.teardown()

    def handle_request(self, request_str):
        request = KittenRequest(request_str)
        self.queue.put(request)
        return request.ack()

    def get_socket(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)

        host = 'tcp://*:{0}'.format(self.ns.port)
        socket.bind(host)
        self.log.info('Listening on {0}', host)

        return socket

    def setup(self):
        self.log.info('Setting up server')
        self.setup_signals()
        self.setup_pidfile()

    def teardown(self):
        if self.torn:
            return

        self.torn = True
        self.log.info('Tearing down server')
        self.teardown_pidfile()

    def setup_signals(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        names = {2: 'SIGINT', 15: 'SIGTERM'}
        self.log.warning('Recieved {0}', names[signum])
        self.teardown()

    @property
    def pidfile(self):
        return conf.pidfile(self.ns.port)

    def setup_pidfile(self):
        pid = str(os.getpid())
        self.log.debug('Pid: {0}', pid)
        with open(self.pidfile, 'w') as pidfile:
            pidfile.write(pid)

    def teardown_pidfile(self):
        self.log.debug('Removing pidfile')
        os.remove(self.pidfile)


def setup_parser(subparsers):
    server = subparsers.add_parser(
        'server',
        help="Start or stop the server"
    )

    sub = server.add_subparsers(help='Server commands', dest="server_command")
    sub.add_parser('start', help='Start the server (default)')
    sub.add_parser('stop', help='Stop the server')

    return execute_parser


def execute_parser(ns):
    if ns.server_command == "stop":
        return stop_server(ns)
    else:
        start_server(ns)


def is_running(ns):
    # Use existence of the pidfile to determine if the server is running
    # TODO: Also check if that PID is actually alive.
    return os.path.isfile(conf.pidfile(ns.port))


def start_server(ns):
    logbook.info('Starting kitten server on port {0}'.format(ns.port))

    validator = kitten.validation.Validator()
    server = KittenServer(ns, validator)
    server.setup()

    gevent.spawn(server.listen_forever)
    gevent.wait()


def stop_server(ns):
    pidfile = conf.pidfile(ns.port)
    if not os.path.exists(pidfile):
        logbook.error('Pidfile {0} not found'.format(pidfile))
        logbook.error('kitten server not running on port {0}'.format(ns.port))
        return 1

    logbook.info('Stopping kitten server on port {0}'.format(ns.port))
    # Send sigint to PIDFILE and let the server gracefully tear down.
    with open(pidfile) as f:
        pid = int(f.read())
        os.kill(pid, signal.SIGINT)

    return 0
