from kitten.client import KittenClient

import mock


class TestClientMessaging(object):
    def setup_method(self, method):
        self.client = KittenClient()
        self.context = mock.MagicMock()
        self.socket = mock.MagicMock()
        self.context.socket.return_value = self.socket

    @mock.patch('zmq.Context')
    def test_simple_send(self, ctx):
        ctx.return_value = self.context
        print(self.socket)

        msg = '{}'
        self.client.send(msg)

        assert self.socket.connect.called
        assert self.socket.send_unicode.call_args_list[0] == mock.call(msg)
        assert self.socket.recv_unicode.called
