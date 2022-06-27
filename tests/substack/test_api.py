import unittest

from substack import Api
from substack.exceptions import SubstackAPIException


class ApiTest(unittest.TestCase):

    def test_api_exception(self):
        with self.assertRaises(SubstackAPIException):
            Api(email="", password="")
