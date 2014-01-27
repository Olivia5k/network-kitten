import json
import logbook
import zmq


class KittenClient(object):
    log = logbook.Logger('KittenClient')

    def send(self, address, msg):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        host = 'tcp://{0}'.format(address)
        socket.connect(host)

        msg = json.dumps(msg)
        self.log.info('Sending request on {1}: {0}', msg, host)
        socket.send_unicode(msg)

        self.log.info('Waiting for reply')
        msg = socket.recv_unicode()
        self.log.info(msg)

        ret = json.loads(msg)

        socket.close()

        return ret
