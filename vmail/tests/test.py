from twisted.trial import unittest
from vmail.model import _create_engine, init_model, init_rw_model

class BaseUnitTest(unittest.TestCase):
    pass

class DatabaseUnitTest(BaseUnitTest):
    """
    Setups up a basic vmail database in order to allow tests to perform
    data manipulation. Each test gets a fresh database.
    """

    def setUp(self):
        engine = _create_engine('sqlite:///')

class CoreUnitTest(DatabaseUnitTest):
    """
    """
