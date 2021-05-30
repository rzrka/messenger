from mainapp.settings import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from mainapp.utils import Message
import json
import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))


class TestSocket:

    def __init__(self, test_dic):
        self.test_dic = test_dic
        self.encoded_message = None
        self.receved_message = None

    def send(self, message):
        json_test_message = json.dumps(self.test_dic)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.receved_message = message

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dic)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        USER: {
            ACCOUNT_NAME: 'test_test'
        }
    }
    test_dict_recv_ok = {RESPONSE: 200}

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict_send)
        message = Message()
        message.send(test_socket, self.test_dict_send)

        self.assertEqual(
            test_socket.encoded_message,
            test_socket.receved_message)

    def test_get(self):
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        message = Message()
        self.assertEqual(message.get(test_sock_ok), self.test_dict_recv_ok)


if __name__ == '__main__':
    unittest.main()
