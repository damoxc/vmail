import os

from vmail.daemon.postfix import Postfix

def test_postfix_queue_stats():
    postfix = Postfix()
    postfix.config['postfix_spool'] = os.path.join(os.path.dirname(__file__), 'spool', 'postfix')
    stats = postfix.queue_stats()

    assert stats['active']   == 0
    assert stats['deferred'] == 78
    assert stats['maildrop'] == 0

def test_postfix_queue_deferred():
    pass
