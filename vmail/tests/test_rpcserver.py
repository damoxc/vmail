import fcntl
import gevent
import datetime
import tempfile

from nose.tools import raises

from vmail.daemon.rpcserver import encode_object
from vmail.daemon.rpcserver import JSONReceiver
from vmail.daemon.rpcserver import RPCMethod

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

@raises(SystemExit)
def test_json_receiver_missing_directory():
    receiver = JSONReceiver('/some/missing/directory')
    receiver.start()

def test_json_receiver_stop_before_start():
    receiver = JSONReceiver('/foo')
    receiver.stop()

class ExportedClass():
    before_test = False
    after_test = False

    def __before__(self):
        self.before_test = True

    def exported_method(self):
        return 5

    def exported_method_fails(self):
        raise Exception('this failed')

    def __after__(self):
        self.after_test = True

def test_rpc_method():
    cls = ExportedClass()
    method = RPCMethod(cls.exported_method)
    assert method() == 5
    assert cls.before_test == True
    assert cls.after_test == True

def test_rpc_method_failure():
    cls = ExportedClass()
    method = RPCMethod(cls.exported_method)
    try:
        assert method()
    except Exception:
        pass

    assert cls.before_test == True
    assert cls.after_test == True
