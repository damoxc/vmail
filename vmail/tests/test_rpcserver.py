import fcntl
import gevent
import datetime
import tempfile

from cStringIO import StringIO

from nose.tools import raises

from vmail.daemon.rpcserver import encode_object
from vmail.daemon.rpcserver import JSONReceiver
from vmail.daemon.rpcserver import RPCMethod
from vmail.error import RPCError

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

class FauxRpcServer(object):

    def dispatch(self, method, args, kwargs):
        pass

@raises(TypeError)
def test_encode_object_invalid():
    encode_object(fcntl)

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

def test_json_receiver_json_handler():
    socket_path = tempfile.mktemp()

    server = FauxRpcServer()

    fobj = StringIO()

    receiver = JSONReceiver(socket_path)
    receiver.set_server(server)
    receiver.handle_json1({
        'id': 1,
        'method': 'test_method',
        'params': []
    }, fobj)

class ExportedClass():
    before_test = False
    after_test = False

    def __before__(self, method):
        self.before_test = True

    def exported_method(self):
        return 5

    def exported_method_fails(self):
        raise RPCError('this failed')

    def exported_method_exception(self):
        raise Exception('unexpected failure')

    def __after__(self, method):
        self.after_test = True

class BadExportedClass(ExportedClass):

    def __before__(self, method):
        raise Exception('before fails')

    def __after__(self, method):
        raise Exception('after fails')

def test_rpc_method():
    cls = ExportedClass()
    method = RPCMethod(cls.exported_method)
    assert method() == 5
    assert cls.before_test == True
    assert cls.after_test == True

def test_rpc_method_failure():
    cls = ExportedClass()
    method = RPCMethod(cls.exported_method_fails)
    try:
        method()
    except RPCError:
        pass

    assert cls.before_test == True
    assert cls.after_test == True

def test_rpc_method_exception():
    cls = ExportedClass()
    method = RPCMethod(cls.exported_method_exception)
    try:
        method()
    except Exception:
        pass

    assert cls.before_test == True
    assert cls.after_test == True

def test_rpc_method_before_after_fails():
    cls = BadExportedClass()
    method = RPCMethod(cls.exported_method)
    assert method() == 5
    assert cls.before_test == False
    assert cls.after_test == False
