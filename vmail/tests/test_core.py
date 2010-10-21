from vmail.tests import test

class TestCore(test.DaemonUnitTest):

    def test_authenticate(self):
        """
        Checks a known user with the correct password to ensure successful
        authenticate.
        """
        def on_authenticate(result):
            self.assertTrue(result)
        return self.client.core.authenticate('dave@example.com', 'daisychain'
            ).addCallback(on_authenticate)

    def test_authenticate_fails(self):
        """
        Checks a known user with the incorrect password to ensure failure
        """
        def on_authenticate(result):
            self.assertFalse(result)
        return self.client.core.authenticate('dave@example.com', 'password'
            ).addCallback(on_authenticate)

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
                ).addCallback(on_checked)
        return self.client.core.block_host('10.20.30.40'
            ).addCallback(on_blocked)

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
            ).addCallback(on_checked)

    def test_check_host_unknown(self):
        """
        Checks an unknown host in the hosts table to ensure there is no
        result returned.
        """
        def on_checked(result):
            self.assertNone(result)
        return self.client.core.check_host('1.2.3.4'
            ).addCallback(on_checked)

    def test_check_whitelist(self):
        """
        Tests checking a known address against the whitelist.
        """
        def on_checked(result):
            self.assertTrue(result)
        return self.client.core.check_whitelist('dumbledore@hogwarts.com'
            ).addCallback(on_checked)

    def test_check_whitelist_unknown(self):
        """
        Tests checking an unknown address against the whitelist.
        """
        def on_checked(result):
            self.assertFalse(result)
        return self.client.core.check_whitelist('snape@hogwarts.com'
            ).addCallback(on_checked)

    def test_get_usage_domain(self):
        """
        Tests checking the usage for a domain.
        """
        def on_got_usage(result):
            self.assertEqual(result, 20656946)
        return self.client.core.get_usage('example.com'
            ).addCallback(on_got_usage)

    def test_get_usage_domain_unknown(self):
        """
        Tests checking the usage for an unknown domain.
        """
        # TODO: Fix this once vmaild has correct email reporting so the
        # exception type is checked etc.
        def on_err_usage(result):
            self.assertNotNone(result)
        return self.client.core.get_usage('higglepuddle.com'
            ).addErrback(on_err_usage)
    
    def test_get_usage_user(self):
        """
        Tests checking the usage for a user.
        """
        def on_got_usage(result):
            self.assertEqual(result, 81998643)
        return self.client.core.get_usage('testing.com', 'fred'
            ).addCallback(on_got_usage)

    def test_get_usage_user_unknown(self):
        """
        Tests checking the usage for an unknown user.
        """
        # TODO: Fix this once vmaild has correct email reporting so the
        # exception type is checked etc.
        def on_err_usage(result):
            self.assertNotNone(result)
        return self.client.core.get_usage('higglepuddle.com', 'yankeedoodle'
            ).addErrback(on_err_usage)

    def test_get_quota_domain(self):
        """
        Tests checking the quota for a domain.
        """
        def on_got_quota(result):
            self.assertEqual(result, 52428800)
        return self.client.core.get_quota('example.com'
            ).addCallback(on_got_quota)

    def test_get_quota_domain_unknown(self):
        """
        Tests checking the quota for a domain.
        """
        # TODO: Fix this once vmaild has correct email reporting so the
        # exception type is checked etc.
        def on_err_quota(result):
            self.assertNotNone(result)
        return self.client.core.get_quota('higglepuddle.com'
            ).addErrback(on_err_quota)
