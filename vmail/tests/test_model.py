from vmail.tests import test
from vmail.model.classes import *

class TestDatabase(test.DatabaseUnitTest):

    def test_domains(self):
        domain = self.db.query(Domain).get(1)
        self.assertTrue(isinstance(domain, Domain))
