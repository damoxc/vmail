from vmail.tests import test

class TestCore(test.DaemonUnitTest):

    def test_authenticate(self):
        def on_authenticate(result):
            self.assertTrue(result)

        return self.client.core.authenticate('dave@example.com', 'daisychain'
            ).addCallback(on_authenticate)
