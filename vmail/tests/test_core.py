from vmail.tests import test
from twisted.python.failure import Failure

class TestCoreSMTP(test.DaemonUnitTest):

    def test_authenticate(self):
        """
        Checks a known user with the correct password to ensure successful
        authenticate.
        """
        return self.client.core.authenticate('dave@example.com', 'daisychain'
            ).addCallback(self.assertTrue
            ).addErrback(self.fail)

    def test_authenticate_fails(self):
        """
        Checks a known user with the incorrect password to ensure failure
        """
        return self.client.core.authenticate('dave@example.com', 'password'
            ).addCallback(self.assertFalse
            ).addErrback(self.fail)

    def test_blocking_host(self):
        """
        Tests adding a host to the block list.
        """
        def on_checked(result):
            self.assertNotNone(result)
            (action, comment) = result
            self.assertEqual(action, 'DENY_DISCONNECT')

        def on_blocked(result):
            self.assertNone(result)
            return self.client.core.check_host('10.20.30.40'
                ).addCallback(on_checked
                ).addErrback(self.fail)

        return self.client.core.block_host('10.20.30.40'
            ).addCallback(on_blocked
            ).addErrback(self.fail)

    def test_blocking_host_already_exists(self):
        """
        Tests adding a host to the block list that is already on it.
        """
        return self.client.core.block_host('43.52.175.8'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_check_host(self):
        """
        Checks a known host in the hosts table and ensure the result is the
        expected one.
        """
        def on_checked(result):
            self.assertNotNone(result)
            (action, comment) = result
            self.assertEqual(action, 'DENY_DISCONNECT')
            self.assertEqual(comment, 'Suspected spam source')

        return self.client.core.check_host('97.38.123.17'
            ).addCallback(on_checked
            ).addErrback(self.fail)

    def test_check_host_unknown(self):
        """
        Checks an unknown host in the hosts table to ensure there is no
        result returned.
        """
        return self.client.core.check_host('1.2.3.4'
            ).addCallback(self.assertNone
            ).addErrback(self.fail)

    def test_check_whitelist(self):
        """
        Tests checking a known address against the whitelist.
        """
        return self.client.core.check_whitelist('dumbledore@hogwarts.com'
            ).addCallback(self.assertTrue
            ).addErrback(self.fail)

    def test_check_whitelist_unknown(self):
        """
        Tests checking an unknown address against the whitelist.
        """
        return self.client.core.check_whitelist('snape@hogwarts.com'
            ).addCallback(self.assertFalse
            ).addErrback(self.fail)

    def test_get_usage_domain(self):
        """
        Tests checking the usage for a domain.
        """
        return self.client.core.get_usage('example.com'
            ).addCallback(self.assertEqual, 20656946
            ).addErrback(self.fail)

    def test_get_usage_domain_unknown(self):
        """
        Tests checking the usage for an unknown domain.
        """
        # TODO: Fix this once vmaild has correct email reporting so the
        # exception type is checked etc.
        return self.client.core.get_usage('higglepuddle.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)
    
    def test_get_usage_user(self):
        """
        Tests checking the usage for a user.
        """
        return self.client.core.get_usage('testing.com', 'fred'
            ).addCallback(self.assertEqual, 81998643
            ).addErrback(self.fail)

    def test_get_usage_user_unknown(self):
        """
        Tests checking the usage for an unknown user.
        """
        # TODO: Fix this once vmaild has correct email reporting so the
        # exception type is checked etc.
        return self.client.core.get_usage('higglepuddle.com', 'yankeedoodle'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_get_quota_domain(self):
        """
        Tests checking the quota for a domain.
        """
        return self.client.core.get_quota('example.com'
            ).addCallback(self.assertEqual, 52428800
            ).addErrback(self.fail)

    def test_get_quota_domain_unknown(self):
        """
        Tests checking the quota for a domain.
        """
        # TODO: Fix this once vmaild has correct email reporting so the
        # exception type is checked etc.
        return self.client.core.get_quota('higglepuddle.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_last_login(self):
        """
        Tests recording a login to the mail system.
        """
        return self.client.core.last_login('dave@example.com', 'imap', '1.2.3.4'
            ).addCallback(self.assertTrue
            ).addErrback(self.fail)

    def test_last_login_unknown(self):
        """
        Tests recording a login to the mail system for an unknown user.
        """
        return self.client.core.last_login('yankeedoodle@higglepuddle.com', 'imap', '1.2.3.4'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_last_login_mixed_case(self):
        """
        Tests recording a login to the mail system for a user but using
        mixed case to ensure it still matches.
        """
        return self.client.core.last_login('Dave@Example.com', 'imap', '1.2.3.4'
            ).addCallback(self.assertTrue
            ).addErrback(self.fail)


class TestCoreManagement(test.DaemonUnitTest):

    def test_delete_forward(self):
        """
        This method tests deleting a forward via the rpc interface.
        """
        def on_deleted(result):
            self.assertNone(result)
            return self.client.core.get_forward('help@example.com'
                ).addCallback(self.fail
                ).addErrback(self.assertIsInstance, Failure)

        return self.client.core.delete_forward('help@example.com'
            ).addCallback(on_deleted
            ).addErrback(self.fail)

    def test_delete_user(self):
        """
        This methods tests deleting a user via the rpc interface.
        """

        def on_deleted(result):
            self.assertNone(result)
            return self.client.core.get_user('dave@example.com'
                ).addCallback(self.fail
                ).addErrback(on_get_user_failed)

        def on_get_user_failed(failure):
            self.assertIsInstance(failure, Failure)
            return self.client.core.get_vacation('dave@example.com'
                ).addCallback(self.fail
                ).addErrback(self.assertIsInstance, Failure)

        return self.client.core.delete_user('dave@example.com'
            ).addCallback(on_deleted
            ).addErrback(self.fail)

    def test_delete_user_unknown(self):
        """
        This method tests deleting an unknown user via the rpc interface.
        """
        return self.client.core.delete_user('dave@example.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_get_forward(self):
        """
        Test getting the forward for the specified address.
        """
        forwards = ['help@example.com']
        return self.client.core.get_forward('info@example.com',
            ).addCallback(self.assertEqual, forwards
            ).addErrback(self.fail)

    def test_get_forward_unknown(self):
        """
        Test getting the forward for an unknown address.
        """
        return self.client.core.get_forward('yankeedoodle@higglepuddle.com',
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_get_forwards(self):
        """
        Test getting the forwards for a domain
        """
        forwards = {
            u'help@example.com': [u'dave@example.com'],
            u'info@example.com': [u'help@example.com']
        }
        return self.client.core.get_forwards('example.com'
            ).addCallback(self.assertEqual, forwards
            ).addErrback(self.fail)

    def test_get_forwards_unknown(self):
        """
        Test getting the forwards for an unknown domain.
        """
        return self.client.core.get_forwards('higglepuddle.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_get_user(self):
        """ 
        This method tests getting the user data via the rpc interface.
        """
        def got_user(user):
            self.assertNotNone(user)
            self.assertTrue(user['enabled'])
            self.assertEqual(user['email'], 'fred@testing.com')

        return self.client.core.get_user('fred@testing.com'
            ).addCallback(got_user
            ).addErrback(self.fail)

    def test_get_user_unknown(self):
        """ 
        This method tests getting the user data via the rpc interface for
        an unknown user.
        """
        return self.client.core.get_user('hinkypinky@testing.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_get_vacation(self):
        """
        Tests getting a vacation message for a user.
        """
        def check_vacation(vacation):
            self.assertNotNone(vacation)
            self.assertEqual(vacation['email'], 'dave@example.com')

        return self.client.core.get_vacation('dave@example.com'
            ).addCallback(check_vacation
            ).addErrback(self.fail)

    def test_get_vacation_unicode(self):
        """
        Tests getting a vacation message that contains unicode characters.
        """

        def check_vacation(vacation):
            self.assertNotNone(vacation)
            self.assertEqual(vacation['email'], 'fred@testing.com')

        return self.client.core.get_vacation('fred@testing.com'
            ).addCallback(check_vacation
            ).addErrback(self.fail)

    def test_get_vacation_missing(self):
        """
        Tests getting a missing vacation message for a user.
        """
        return self.client.core.get_vacation('fred@testing.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_get_vacation_unknown(self):
        """
        Tests getting a vacation message for an unknown user.
        """
        return self.client.core.get_vacation('hinkypinky@testing.com'
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)

    def test_save_forward(self):
        """
        Test saving a forward and then checking to ensure that what we saved
        matches what is returned by core.get_forward.
        """
        source = 'sales@example.com'
        destinations = ['dave@example.com']

        def on_added_forward(source_):
            self.assertEqual(source_, source)
            return self.client.core.get_forward(source_
                ).addCallback(self.assertEqual, destinations
                ).addErrback(self.fail)

        return self.client.core.save_forward(1, source, destinations
            ).addCallback(on_added_forward
            ).addErrback(self.fail)

    def test_save_forward_unknown(self):
        """
        Tests saving a forward for an unknown domain.
        """

        source = 'yankeedoodle@higglepuddle.com'
        destinations = ['help@higglepuddle.com']

        return self.client.core.save_forward(5, source, destinations
            ).addCallback(self.fail
            ).addErrback(self.assertIsInstance, Failure)
