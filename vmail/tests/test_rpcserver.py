import fcntl
import gevent
import datetime
import tempfile

from nose.tools import raises

from vmail.daemon.rpcserver import encode_object
from vmail.daemon.rpcserver import JSONReceiver

def test_encode_object():
    date = datetime.datetime(2011, 10, 24)
    assert encode_object(date) == {
        'isdst': -1,
        'mday': 24,
        'hour': 0,
        'min': 0,
        'sec': 0,
        'mon': 10,
        'year': 2011,
        'yday': 297,
        'wday': 0
    }

@raises(TypeError)
def test_encode_object_invalid():
    class Invalid:
        pass
    encode_object(Invalid())

def test_encode_object_json():
    class Test(object):
        def __json__(self):
            return {'test': True}

    assert encode_object(Test()) == {'test': True}

@raises(SystemExit)
def test_json_receiver_permission_denied():
    receiver = JSONReceiver('/socket')
    receiver.start()

@raises(SystemExit)
def test_json_receiver_already_running():
    socket_path = tempfile.mktemp()
    fp = open(socket_path + '.lck', 'a+')
    fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)

    receiver = JSONReceiver(socket_path)
    receiver.start()
