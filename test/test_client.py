import pytest
import mock
from test import MockKittenClientMixin

from kitten.server import RequestError


class TestClientMessaging(MockKittenClientMixin):
    def setup_method(self, method):
        super(TestClientMessaging, self).setup_method(method)

    @mock.patch('zmq.Poller')
    @mock.patch('zmq.Context')
    def test_simple_send(self, ctx, poller):
        ctx.return_value = self.context

        self.socket.recv_unicode.return_value = '{"hehe": true}'
        poller.return_value.poll.return_value = [(self.socket, 1)]
        ret = self.client.send('hehe:1234', {})

        assert ret == {'hehe': True}
        assert self.socket.connect.called
        assert self.socket.send_unicode.called_once_with('{}')
        assert self.socket.recv_unicode.called

    @mock.patch('zmq.Poller')
    @mock.patch('zmq.Context')
    def test_simple_send_times_out(self, ctx, poller):
        ctx.return_value = self.context

        self.socket.recv_unicode.return_value = '{"hehe": true}'
        poller.return_value.poll.return_value = []

        with pytest.raises(RequestError):
            self.client.send('hehe:1234', {})
