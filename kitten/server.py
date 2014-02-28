import sys
import os
import json
import signal
import zmq.green as zmq
import logbook

import gevent
from gevent.pool import Pool
from gevent.queue import Queue

from kitten import conf
from kitten.request import KittenRequest


class KittenServer(object):
    log = logbook.Logger('KittenServer')

    def __init__(self, ns):
        self.ns = ns
        self.pool = Pool(5)
        self.queue = Queue()
        self.working = None

    def listen(self, socket):
        request_str = socket.recv_unicode()
        # Send the request for processing and handle any errors
        response = self.handle_request(request_str)

        # Dump as JSON string and send it back
        response_str = json.dumps(response)
        socket.send_unicode(response_str)

        return True

    def listen_forever(self):
        try:
            socket = self.get_socket()
            while self.listen(socket):
                pass

        except Exception:
            self.log.exception('Server died.')

        finally:
            self.teardown()

    def handle_request(self, request_str):
        request = KittenRequest(request_str)
        self.queue.put(request)
        return request.ack()

    def work(self):
        if self.queue.empty():
            self.log.debug('About to sleep')
            gevent.sleep(1.0)  # TODO: Configurable
            self.log.debug('Slept')
            return True

        request = self.queue.get()
        socket = self.get_socket(zmq.REQ, request.host)
        self.pool.spawn(request.process, socket)

        return True

    def work_forever(self):
        self.working = True

        while self.work():
            pass  # pragma: nocover

        self.working = False
        self.log.warning('Worker pool stopped.')

    def teardown_workers(self):
        free = self.pool.free_count()
        if free == self.pool.size:
            self.log.info('Workers idle.')
            return True

        timeout = 5  # TODO: Configurable
        count = self.pool.size - free
        self.log.info('Giving {1} requests {0}s to finish', timeout, count)
        self.pool.kill(timeout=timeout)
        self.log.info('Requests finished or timed out.')

    def get_socket(self, kind=zmq.REP, host=None):
        context = zmq.Context()
        socket = context.socket(kind)

        if not host:
            host = 'tcp://*:{0}'.format(self.ns.port)

        socket.bind(host)
        self.log.info(
            'Bound {1} on {0}',
            host,
            {zmq.REP: 'REP', zmq.REQ: 'REQ'}.get(kind, kind)
        )

        return socket

    def setup(self):
        self.log.info('Setting up server')
        self.setup_signals()
        self.setup_pidfile()

    def teardown(self):
        self.log.info('Tearing down server')
        self.teardown_workers()
        self.teardown_pidfile()
        self.log.info('Server torn. Exiting.')
        sys.exit(0)

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

    server = KittenServer(ns)
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
