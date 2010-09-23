from vmail.tests import test
from vmail.model import *

class TestDatabase(test.DatabaseUnitTest):

    def test_domains(self):
        domain = db.query(Domain).get(1)
        self.assertTrue(isinstance(domain, Domain))
