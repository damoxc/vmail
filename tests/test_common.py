from twisted.trial import unittest
from vmail.common import *

class CommonTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fsize(self):
        self.failUnless(fsize(112245) == '109.6 KiB')

    def test_address_parse(self):
        addr = Address.parse('John Smith <john.smith@example.com>')
        self.failUnless(addr.address == 'john.smith@example.com')
        self.failUnless(addr.name == 'John Smith')
        self.failUnless(addr.user == 'john.smith')
        self.failUnless(addr.host == 'example.com')
        self.failUnless(str(addr) == 'John Smith <john.smith@example.com>')

        self.failUnlessRaises(VmailError, Address.parse, 'broken email')

    def test_address(self):
        addr = Address('john.smith@example.com', 'John Smith')
        self.failUnless(addr.address == 'john.smith@example.com')
        self.failUnless(addr.name == 'John Smith')
        self.failUnless(addr.user == 'john.smith')
        self.failUnless(addr.host == 'example.com')
        self.failUnless(str(addr) == 'John Smith <john.smith@example.com>')
