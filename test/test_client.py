import pytest
import mock
from test.utils import MockKittenClientMixin

from kitten.server import RequestError


class TestClientMessaging(MockKittenClientMixin):
    def setup_method(self, method):
        super(TestClientMessaging, self).setup_method(method)

    @mock.patch('zmq.green.Poller')
    @mock.patch('zmq.green.Context')
    def test_simple_send(self, ctx, poller):
        ctx.return_value = self.context

        self.socket.recv_unicode.return_value = '{"hehe": true}'
        poller.return_value.poll.return_value = [(self.socket, 1)]
        ret = self.client.send('hehe:1234', {})

        assert ret == {'hehe': True}
        assert self.socket.connect.called
        assert self.socket.recv_unicode.called
        self.socket.send_unicode.assert_called_once_with('{}')

    @mock.patch('zmq.green.Poller')
    @mock.patch('zmq.green.Context')
    def test_simple_send_times_out(self, ctx, poller):
        ctx.return_value = self.context

        self.socket.recv_unicode.return_value = '{"hehe": true}'
        poller.return_value.poll.return_value = []

        with pytest.raises(RequestError):
            self.client.send('hehe:1234', {})
