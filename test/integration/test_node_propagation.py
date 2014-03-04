from kitten.client import KittenClient
from kitten.server import KittenServer

from mock import MagicMock


class TestPropagation(object):
    def setup_method(self, method):
        self.servers = []
        self.port = 9812
        self.request = {
            'hehe': True
        }

        for port in range(4):
            ns = MagicMock()
            ns.port = self.port + port

            server = KittenServer(ns)
            self.servers.append(server)

    def teardown_method(self, method):
        return
        map(lambda s: s.stop(exit=False), self.servers)

    def test_node_propagation(self):
        """
        Tests that check node propagation

        1) Spin up four servers.
        2) Make the first one send a sync request to all three others.
        3) Count the numbers of requests made.
        4) Check databases to see that they all know each other.

        """

        return

        map(lambda s: s.start(), self.servers)

        client = KittenClient()
        response = client.send('localhost:{0}'.format(self.port), self.request)
        print(response)
