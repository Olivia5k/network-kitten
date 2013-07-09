import json
import unittest

from wolf.server import WolfServer
from wolf.server import RequestException


class MockParadigm(object):
    def fake(self, request):
        return {
            'code': 'OK'
        }


class ServerIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.server = WolfServer()
        self.server.paradigms = {
            'mock': MockParadigm()
        }

    def test_handle_request(self):
        request = json.dumps({'paradigm': 'mock', 'method': 'fake'})
        result = self.server.handle_request(request)
        self.assertEqual(result, {'code': 'OK'})

    def test_handle_request_invalid_json(self):
        request = '{'
        self.assertRaises(
            RequestException,
            self.server.handle_request,
            request
        )
