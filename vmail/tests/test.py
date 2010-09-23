from twisted.trial import unittest

class BaseUnitTest(unittest.TestCase):
    pass

class DatabaseUnitTest(BaseUnitTest):
    """
    Setups up a basic vmail database in order to allow tests to perform
    data manipulation. Each test gets a fresh database.
    """

    def setUp(self):
        from vmail.model import _create_engine, init_model, init_rw_model
        from vmail.model.tables import *
        engine = _create_engine('sqlite:///')
        meta.create_all(bind=engine)

        init_model(engine)
        init_rw_model(engine)

class CoreUnitTest(DatabaseUnitTest):
    """
    """
