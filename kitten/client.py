import json
import logbook
import zmq.green as zmq

from kitten.request import RequestError


class KittenClient(object):
    log = logbook.Logger('KittenClient')
    timeout = 2000

    def send(self, address, request):
        self.log.info('Sending request on {1}: {0}', request, address)
        socket = self.connect(address)
        socket.send_json(request)
        self.log.info('Waiting for reply')

        events = self.poll_reply(socket)

        if not events:
            msg = 'Timeout after {0}ms'.format(self.timeout)
            self.log.error(msg)
            self.close(socket)
            raise RequestError('TIMEOUT', msg)

        # TODO: Can JSON events come in multiparts? Probably not?
        response = events[0][0].recv_json()

        self.log.info(response)
        self.close(socket)

        return response

    def close(self, socket):
        socket.close()

        # TODO: Figure out why destroying the context makes the application
        # hang indefinetely.
        # self.context.destroy()
        # del self.context

    def connect(self, address):
        self.context = zmq.Context()
        socket = self.context.socket(zmq.REQ)

        host = 'tcp://{0}'.format(address)
        socket.connect(host)

        return socket

    def poll_reply(self, socket):
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        events = poller.poll(self.timeout)

        return events
