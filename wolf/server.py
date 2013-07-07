import json
import logging
import zmq

from wolf.paradigm.shasum import ShasumParadigm

PORT = 5555
logging.basicConfig(level=logging.DEBUG)


class WolfServer(object):
    log = logging.getLogger('WolfServer')

    def __init__(self):
        self.paradigms = {}

    def listen_forever(self, port=PORT):
        context = zmq.Context()
        socket = context.socket(zmq.REP)

        host = 'tcp://*:{0}'.format(port)
        socket.bind(host)
        self.log.info('Listening on %s', host)

        while True:
            request = socket.recv_unicode()
            response = self.handle_request(request)
            socket.send_unicode(response)
            print()

    def setup(self):
        self.log.info('Setting up server')
        self.paradigms = self.get_paradigms()

    def get_paradigms(self, *paradigms):
        self.log.info('Loading paradigms')
        return {
            'shasum': ShasumParadigm()
        }

    def validate_request(self, request):
        self.log.info('Validating request...')

    def validate_response(self, response):
        self.log.info('Validating response...')

    def handle_request(self, request_str):
        """
        Handle a request.

        This is the meat of the server. This function will take an incoming
        request, decode it, validate it, send it to the appropriate paradigm
        and handler, get the response, validate the response, encode the
        response and return it back to the server.

        """

        self.log.info('Getting new request...')
        request = json.loads(request_str)
        self.log.debug('Got request: %s', request)

        self.validate_request(request)

        paradigm_name = request['paradigm']
        method_name = request['method']

        paradigm = self.paradigms[paradigm_name]
        method = getattr(paradigm, method_name, None)

        response = method(request)
        self.validate_response(response)

        response = json.dumps(response)
        self.log.debug('Returning response: %s', response)
        return response


def main():
    logging.info('Starting wolf server')
    server = WolfServer()
    server.setup()

    server.listen_forever()

if __name__ == "__main__":
    main()
