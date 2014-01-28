import json
import logbook
import zmq

from kitten.server import RequestError


class KittenClient(object):
    log = logbook.Logger('KittenClient')
    timeout = 2000

    def send(self, address, request):
        request = json.dumps(request)

        self.log.info('Sending request on {1}: {0}', request, address)
        socket = self.connect(address)
        socket.send_unicode(request)
        self.log.info('Waiting for reply')

        events = self.poll_reply(socket)

        if not events:
            msg = 'Timeout after {0}ms'.format(self.timeout)
            self.log.error(msg)
            self.close(socket)
            raise RequestError('TIMEOUT', msg)

        response = ''.join(t[0].recv_unicode() for t in events)
        ret = json.loads(response)

        self.log.info(ret)
        self.close(socket)

        return ret

    def close(self, socket):
        socket.close()
        self.context.destroy()
        del self.context

    def connect(self, address):
        self.context = zmq.Context()
        socket = self.context.socket(zmq.XREQ)  # XXX: Read up on XREQ

        host = 'tcp://{0}'.format(address)
        socket.connect(host)

        return socket

    def poll_reply(self, socket):
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        events = poller.poll(self.timeout)

        return events
