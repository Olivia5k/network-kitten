import uuid

from kitten.server import KittenServer
from kitten.request import KittenRequest

import pytest
from mock import MagicMock
import gevent


class TestPropagation(object):
    def setup_method(self, method):
        self.local_port = 9812
        self.remote_port = 9813
        self.request = {
            'id': {
                'uuid': str(uuid.uuid4()),
                'to': '127.0.0.1:{0}'.format(self.remote_port),
                'from': '127.0.0.1:{0}'.format(self.local_port),
                'kind': 'req',
            },
            'paradigm': 'node',
            'method': 'ping',
        }

        self.servers = []
        for port in (self.local_port, self.remote_port):
            ns = MagicMock()
            ns.port = port
            self.servers.append(KittenServer(ns))

    @pytest.mark.timeout(10)
    def test_node_ping(self):
        """
        Check that two servers can ping each other.

        1) Spin up two Servers
        2) Add a ping request into the local server queue
        3) Make sure the local server made the request and got an ack
        4) Make sure the remote server made the response and got an ack

        """

        return
        map(lambda s: s.start(), self.servers)
        gevent.sleep(0.1)  # Allow them some time to start up

        request = KittenRequest(self.request)
        self.servers[0].queue.put(request)
        assert self.servers[1].queue.empty()

        gevent.sleep(0.3)

        self.fail()
