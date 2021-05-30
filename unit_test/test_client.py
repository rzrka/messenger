from mainapp.settings import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import Client
import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))


class TestClient(unittest.TestCase):

    def test_presense(self):
        test = Client().create_presense()
        test[TIME] = 1.1
        self.assertEqual(
            test, {
                ACTION: PRESENCE, TIME: 1.1, USER: {
                    ACCOUNT_NAME: 'Guest'}})

    def test_no_presense(self):
        test = Client().create_presense()
        self.assertNotEqual(
            test, {
                ACTION: PRESENCE, TIME: 1.1, USER: {
                    ACCOUNT_NAME: 'Guest'}})

    def test_200_ans(self):
        self.assertEqual(Client().process_ans(
            {RESPONSE: 200}), '\033[0;32m200 : OK')

    def test_400_ans(self):
        self.assertEqual(Client().process_ans(
            {RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')


if __name__ == '__main__':
    unittest.main()
