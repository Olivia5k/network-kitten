import mock
from test import MockKittenClientMixin


class TestClientMessaging(MockKittenClientMixin):
    def setup_method(self, method):
        super(TestClientMessaging, self).setup_method(method)

    @mock.patch('zmq.Context')
    def test_simple_send(self, ctx):
        ctx.return_value = self.context

        self.socket.recv_unicode.return_value = '{"hehe": true}'
        ret = self.client.send({})

        assert ret == {'hehe': True}
        assert self.socket.connect.called
        assert self.socket.send_unicode.called_once_with('{}')
        assert self.socket.recv_unicode.called
        assert self.socket.recv_unicode.called
