from twisted.internet import reactor, threads

from vmail.tests import test
from vmail.model.classes import *

class TestDatabase(test.DatabaseUnitTest):

    def test_domain(self):
        domain = self.db.query(Domain).get(1)
        self.assertTrue(isinstance(domain, Domain))

    def test_domain_deletion(self):
        domain = self.db.query(Domain).get(1)
        self.db.delete(domain)
        self.db.commit()

        # Check the forwards have been removed
        self.assertEqual(self.db.query(Forwards
            ).filter_by(domain_id=1
            ).count(), 0)

        # Check that the transports have been removed
        self.assertEqual(self.db.query(Transport
            ).filter_by(domain_id=1
            ).count(), 0)
        
        # Check the users have been removed
        self.assertEqual(self.db.query(User
            ).filter_by(domain_id=1
            ).count(), 0)

    def test_user(self):
        user = self.db.query(User).get(1)
        self.assertTrue(isinstance(user, User))

    def test_user_creation(self):
        usage = UserQuota()
        usage.bytes = 123123
        usage.messages = 83

        user_count = self.db.query(User).count()

        user = User()
        user.domain_id = 1
        user.email = 'joe.bloggs@example.com'
        user.name = 'Joe Bloggs'
        user.password = 'somesecret'
        user.quota = 52428800
        user.usage = usage
        self.db.add(user)
        self.db.commit()

        _user = self.db.query(User
            ).filter_by(email='joe.bloggs@example.com'
            ).one()
        self.assertTrue(user_count < self.db.query(User).count())
        self.assertEqual(_user.name, 'Joe Bloggs')
        self.assertEqual(_user.usage.bytes, 123123)

    def test_user_deletion(self):
        user_count = self.db.query(User).count()
        user = self.db.query(User).get(4)
        self.db.delete(user)
        self.db.commit()

        # Check that the user has indeed been removed from the database
        self.assertTrue(user_count > self.db.query(User).count())

        # Check that the user_quota entry has also been removed
        self.assertNone(self.db.query(UserQuota
            ).filter_by(email='fred@testing.com'
            ).first())

    def test_vacation(self):
        vacation = self.db.query(Vacation).get(1)
        self.assertTrue(isinstance(vacation, Vacation))

    def test_vacation_deletion(self):
        vacation = self.db.query(Vacation).get(1)
        email = vacation.email

        self.db.delete(vacation)
        self.db.commit()

        self.assertEqual(self.db.query(VacationNotification
            ).filter_by(on_vacation=email
            ).count(), 0)

class TestSessionPool(test.ThreadedDatabaseUnitTest):

    def test_same_object_across_threads(self):
        """
        Test using a session to access an object, checking it back in 
        and then opening a new session accessing the same object.
        """
        from vmail.model import rw_pool

        def get_vacation():
            rw_db = rw_pool.checkout()
            user = rw_db.query(User).get(2)
            rw_pool.checkin()
            return True

        def get_user():
            rw_db = rw_pool.checkout()
            user = rw_db.query(User).get(2)
            rw_db.delete(user.vacation)
            rw_pool.checkin()
            return True

        threads.deferToThread(get_vacation)
        return threads.deferToThread(get_user)

class TestProcedures(test.DatabaseUnitTest):

    def setUp(self):
        super(TestProcedures, self).setUp()
        from vmail.model import procs
        procs.db = self.db
        procs.rw_db = self.rw_db
        self.procs = procs
    
    def test_get_quotas(self):
        self.assertEqual(self.procs.get_quotas('dave@example.com'
            ), (52428800L, 52428800L))
    
    def test_is_validrcptto(self):
        self.assertEqual(self.procs.is_validrcptto('dave@example.com'
            ), (0, 'dave@example.com', 'local'))
    
    def test_process_forwards(self):
        """
        Tests adding a new forward to model and then processing
        """
        # Firstly add a new forward to the model
        forward = Forward()
        forward.domain_id = 1
        forward.source = 'info@example.com'
        forward.destination = 'postmaster@example.com'
        self.rw_db.add(forward)
        self.rw_db.commit()

        # Process the forwards
        self.procs.process_forwards()

        # Make sure that the forwardings table contains the new forward
        # destination
        fwd = self.rw_db.query(Forwards
            ).filter_by(source=forward.source
            ).first()

        self.assertEqual(len(fwd.destination.split(',')), 2)

    def test_resolve_forwards(self):
        # Firstly add a new forward to the model
        forward = Forward()
        forward.domain_id = 1
        forward.source = 'info@example.com'
        forward.destination = 'postmaster@example.com'
        self.rw_db.add(forward)
        self.rw_db.commit()

        # Process the forwards
        self.procs.resolve_forwards()

        # Make sure that the forwardings table contains the new forward
        # destination
        fwd = self.rw_db.query(Forwards
            ).filter_by(source=forward.source
            ).first()

        self.assertEqual(len(fwd.destination.split(',')), 2)
