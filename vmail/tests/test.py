import os
import gevent
import shutil
import logging
import tempfile
import unittest

import gevent
import gevent.greenlet

from gevent.hub import GreenletExit
from gevent.monkey import patch_all; patch_all()

class QuietGreenlet(gevent.greenlet.Greenlet):

    def _report_error(self, exc_info):
        exception = exc_info[1]
        if isinstance(exception, GreenletExit):
            self._report_result(exception)
            return

        self._exception = exception
        if self._links and self._notifier is None:
            self._notifier = gevent.core.active_event(self._notify_links)

gevent.Greenlet = gevent.greenlet.Greenlet = QuietGreenlet
reload(gevent)

from vmail.tests import testdata
from vmail.model.tables import *

logging.basicConfig(
    level  = logging.ERROR,
    format = '%(asctime)s %(levelname)s [%(funcName)s] %(message)s'
)

class BaseUnitTest(unittest.TestCase):

    def setUp(self):
        self.testDir = tempfile.mkdtemp()
        os.chdir(self.testDir)

    def tearDown(self):
        shutil.rmtree(self.testDir)

    def failUnlessNone(self, expr, msg=None):
        """
        Fail the test unless the expression is None.
        """
        if expr is not None:
            raise self.failureException, msg

    def failIfNone(self, expr, msg=None):
        """
        Fail the test if the expression is None.
        """
        if expr is None:
            raise self.failureException, msg

    # Synonyms for assertion methods
    assertNone = failUnlessNone
    assertNotNone = failIfNone

class DatabaseUnitTest(BaseUnitTest):
    """
    Setups up a basic vmail database in order to allow tests to perform
    data manipulation. Each test gets a fresh database.
    """

    def _create_engine(self):
        from vmail.model import _create_engine
        return _create_engine('sqlite:///')

    def setUp(self):
        super(DatabaseUnitTest, self).setUp()
        from vmail.model import init_model, init_rw_model
        engine = self._create_engine()

        # Create the database schema
        meta.bind = engine
        meta.create_all()

        # Insert some test data into the database
        for (name, quota, account_limit) in testdata.packages:
            packages.insert().values(
                name          = name,
                quota         = quota,
                account_limit = account_limit
            ).execute()

        for (domain, package, package_id, quota, account_limit) in testdata.domains:
            domains.insert().values(
                domain        = domain,
                package       = package,
                package_id    = package_id,
                quota         = quota,
                account_limit = account_limit
            ).execute()

        for (domain_id, email, se, name, password, cleartext, quota, enabled, admin) in testdata.users:
            users.insert().values(
                domain_id       = domain_id,
                email           = email,
                secondary_email = se,
                name            = name,
                password        = password,
                cleartext       = cleartext,
                quota           = quota,
                enabled         = enabled,
                admin           = admin
            ).execute()

        for (email, bytes, messages) in testdata.user_quotas:
            user_quotas.insert().values(
                email    = email,
                bytes    = bytes,
                msesages = messages
            ).execute()

        for (email, subject, body, created, active) in testdata.vacation:
            vacation.insert().values(
                email   = email,
                subject = subject,
                body    = body,
                created = created,
                active  = active
            ).execute()

        for (on_vacation, notified, notified_at) in testdata.vacation_notification:
            vacation_notification.insert().values(
                on_vacation = on_vacation,
                notified    = notified,
                notified_at = notified_at
            ).execute()

        for (domain_id, source, destination) in testdata.forwardings:
            forwardings.insert().values(
                domain_id     = domain_id,
                source        = source,
                destination   = destination
            ).execute()

        for (domain_id, source, destination) in testdata.forwards:
            forwards.insert().values(
                domain_id     = domain_id,
                source        = source,
                destination   = destination
            ).execute()

        for (domain_id, source, transport_) in testdata.transport:
            transport.insert().values(
                domain_id = domain_id,
                source    = source,
                transport = transport_
            ).execute()

        for (email, user_id, method, local_addr, remote_addr, date) in testdata.logins:
            logins.insert().values(
                email       = email,
                user_id     = user_id,
                method      = method,
                local_addr  = local_addr,
                remote_addr = remote_addr,
                date        = date
            ).execute()

        for (ip_address, action, comment) in testdata.hosts:
            hosts.insert().values(
                ip_address = ip_address,
                action     = action,
                comment    = comment
            ).execute()

        for address in testdata.blacklist:
            blacklist.insert().values(address=address).execute()

        for address in testdata.whitelist:
            whitelist.insert().values(address=address).execute()

        mysql_sucks.insert().values(test=1).execute()

        # Initialize the sessions
        init_model(engine)
        init_rw_model(engine)

        # Set the db and rw_db as local variables to avoid auto-connecting
        from vmail.model import db, rw_db
        self.db = db
        self.rw_db = rw_db

    def tearDown(self):
        meta.drop_all()
        super(DatabaseUnitTest, self).tearDown()

class ThreadedDatabaseUnitTest(DatabaseUnitTest):
    """
    Creates a sqlite engine as a file to allow for threaded tests to be
    run.
    """

    def _create_engine(self):
        from vmail.model import _create_engine
        db_path = os.path.join(self.testDir, 'test.db')
        return _create_engine('sqlite:///' + db_path)

class DaemonUnitTest(DatabaseUnitTest):
    """
    Starts a Vmail Daemon within the test suite.
    """

    def setUp(self):
        super(DaemonUnitTest, self).setUp()
        from vmail.client import Client
        from vmail.daemon.rpcserver import RPCServer, JSONReceiver
        from vmail.daemon.core import Core
        from vmail.daemon.qpsmtpd import Qpsmtpd

        self.rpcserver = RPCServer()
        self.rpcserver.register_object(Core(None))
        self.rpcserver.register_object(Qpsmtpd())
        self.rpcserver.add_receiver(JSONReceiver('vmaild.sock'))
        self.rpcserver.start()
        gevent.sleep()

        self.client = Client('vmaild.sock')
        self.client.connect()

    def tearDown(self):
        self.client.disconnect()
        self.rpcserver.stop()
        super(DaemonUnitTest, self).tearDown()
        return
