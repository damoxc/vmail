from twisted.trial import unittest
from vmail.model.tables import *

class BaseUnitTest(unittest.TestCase):
    pass

class DatabaseUnitTest(BaseUnitTest):
    """
    Setups up a basic vmail database in order to allow tests to perform
    data manipulation. Each test gets a fresh database.
    """

    def setUp(self):
        from vmail.model import _create_engine, init_model, init_rw_model
        engine = _create_engine('sqlite:///')
        meta.create_all(bind=engine)

        init_model(engine)
        init_rw_model(engine)

        from vmail.model import db, rw_db
        self.db = db
        self.rw_db = rw_db

class CoreUnitTest(DatabaseUnitTest):
    """
    """
