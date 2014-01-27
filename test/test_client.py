import mock
from test import MockKittenClientMixin


class TestClientMessaging(MockKittenClientMixin):
    def setup_method(self, method):
        super(TestClientMessaging, self).setup_method(method)

    @mock.patch('zmq.Context')
    def test_simple_send(self, ctx):
        ctx.return_value = self.context

        msg = '{}'
        self.client.send(msg)

        assert self.socket.connect.called
        assert self.socket.send_unicode.call_args_list[0] == mock.call(msg)
        assert self.socket.recv_unicode.called
