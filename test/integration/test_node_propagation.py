from kitten.server import KittenServer

from gevent.pool import Group

from mock import MagicMock


class TestPropagation(object):
    def setup_method(self, method):
        self.servers = Group()

        for port in range(4):
            ns = MagicMock()
            ns.port = 9812 + port

            server = KittenServer(ns)
            self.servers.spawn(server.listen_forever)

    def teardown_method(self, method):
        self.servers.kill(timeout=1)

    def test_node_propagation(self):
        """
        Tests that check node propagation

        1) Spin up four servers.
        2) Make the first one send a sync request to all three others.
        3) Count the numbers of requests made.
        4) Check databases to see that they all know each other.

        """

        pass
