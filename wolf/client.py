import json
import logbook
import zmq

from wolf.conf import PORT


class WolfClient(object):
    log = logbook.Logger('WolfClient')

    def send(self, msg, port=PORT):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        host = 'tcp://localhost:{0}'.format(port)
        socket.connect(host)

        self.log.info('Sending request on {1}: {0}', msg, host)
        socket.send_unicode(msg)

        self.log.info('Waiting for reply')
        msg = socket.recv_unicode()
        self.log.info(msg)


def main():
    msg = json.dumps({'paradigm': 'shasum', 'method': 'ping'})
    WolfClient().send(msg)


if __name__ == '__main__':
    main()
