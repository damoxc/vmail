#
# vmail/daemon/main.py
#
# Copyright (C) 2010-2012 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2012 Damien Churchill <damoxc@gmail.com>
#
# Based off rpcserver.py found in Deluge, written by Andrew Resch.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.    If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA    02110-1301, USA.
#

import os
import sys
import json
import stat
import errno
import fcntl
import gevent
import logging
import datetime

from gevent import socket
from gevent.server import StreamServer

from vmail import common
from vmail.error import VmailError, RPCException, RPCError

log = logging.getLogger(__name__)

def encode_object(obj):
    if isinstance(obj, datetime.datetime):
        tt = obj.timetuple()
        return dict([(k[3:], getattr(tt, k)) for k in dir(tt) if k[0:2] == 'tm'])
    if not isinstance(obj, object):
        raise TypeError(repr(obj) + " is not JSON serializable")
    __json__ = getattr(obj, '__json__', None)
    if not __json__:
        raise TypeError(repr(obj) + " is not JSON serializable")
    return __json__()

def export(func, *args ,**kwargs):
    func._rpcserver_export = True
    doc = func.__doc__
    func.__doc__ = '**RPC Exported Function** \n\n'
    if doc:
        func.__doc__ += doc
    return func

class Receiver(object):

    server = None

    def set_server(self, server):
        """
        Set the server instance this receiver is receiving for.

        :param server: The server instance
        :type server: `RPCServer`
        """
        self.server = server

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

class JSONReceiver(Receiver):
    """
    This receiver implements the standard JSON-RPC api into Vmail.
    """

    def __init__(self, socket_path=None):
        self.config   = common.get_config()
        self.lockfile = None
        self.requests = {}
        self.socket_path = socket_path

        if self.socket_path:
            self.socket_path = os.path.abspath(self.socket_path)
        self._server = None

    def handle(self, sock, addr):
        """
        Handler for the gevent StreamServer.

        :param sock: The client socket
        :type sock: `gevent.socket.socket`
        :param addr: The address of the remote client
        :type addr: `tuple`
        """
        log.debug('client has connected')
        fobj = sock.makefile()
        buf = ''

        # Enter the mainloop for this connection
        while True:
            try:
                data = fobj.readline()
                if not data:
                    break # Client has disconnected
            except socket.error:
                break # there's been an error

            try:
                buf += data
                request = json.loads(buf)
                buf = ''
            except ValueError as e:
                log.exception(e)
                continue

            if type(request) is not dict:
                log.info('Received invalid message: type is not dict')
                continue

            if 'method' not in request:
                log.debug('Received invalid request: missing method name')
                continue

            json_version = request.get('jsonrpc')
            if json_version == '2.0':
                self.handle_json2(request, fobj)
            else:
                self.handle_json1(request, fobj)

        # Shutdown the socket
        log.debug('client has disconnected')
        try:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except socket.error as e:
            if e.errno != errno.ENOTCONN:
                raise

    def handle_json1(self, request, fobj):
        # Get the required parameters for our method call
        method     = request['method']
        request_id = request.get('id')
        params     = request.get('params')

        # Dispatch the call
        g = gevent.spawn(self.server.dispatch, method, params)
        g.link(self.respond_json1)
        self.requests[g] = (request, fobj)

    def handle_json2(self, request, fobj):
        # Get the required parameters for our method call
        method     = request['method']
        request_id = request.get('id')
        params     = request.get('params')

        if type(params) is list:
            args   = params
            kwargs = {}
        elif type(params) is dict:
            args   = []
            kwargs = params

        # Dispatch the call
        g = gevent.spawn(self.server.dispatch, method, args, kwargs)
        g.link(self.respond_json2)
        self.requests[g] = (request, fobj)

    def respond_json1(self, response):
        """
        Handles the result of a JSON-RPCv1 call.

        :param response: The finished Greenlet containing the response.
        :type response: Greenlet
        """
        # Retrieve and remove the request id
        request, sock = self.requests.pop(response)

        # Get the correct return value
        result = None
        error  = None
        try:
            result = response.get()
        except Exception as e:
            if not isinstance(e, RPCError):
                log.exception(e, {'request': request})

            error = {
                'name': e.__class__.__name__,
                'message': ''
            }

        # Create the json encoded response string
        data = json.dumps({
            'id': request['id'],
            'result': result,
            'error': error
        }, default=encode_object)

        try:
            sock.write(data + '\r\n')
            sock.flush()
        except socket.error as e:
            # An EPIPE error occurs when a client disconnects uncleanly
            # but we aren't too bothered about this so silence the noise
            if e.errno == errno.EPIPE:
                return
            raise

    def respond_json2(self):
        pass

    def start(self):
        socket_path = self.socket_path or self.config['socket']

        if not os.path.isdir(os.path.dirname(socket_path)):
            log.fatal('Cannot create socket: directory missing')
            exit(1)

        # We want to check if another instance is running
        try:
            self.lockfile = open(socket_path + '.lck', 'a+')
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            if e.errno == errno.EAGAIN:
                log.fatal('Another instance of vmaild is already running')
                exit(1)
            elif e.errno == errno.EACCES:
                log.fatal('Permission denied checking the lock file')
                exit(1)
            else:
                raise
        else:
            if os.path.exists(socket_path):
                os.remove(socket_path)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(0)
        sock.bind(socket_path)
        sock.listen(400)

        os.chmod(socket_path,
            stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO | stat.S_ISGID)

        self._server = StreamServer(sock, self.handle)
        self._server.serve_forever()

    def stop(self):
        if self._server:
            self._server.stop()

        if self.lockfile:
            os.remove(self.lockfile.name)
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_UN)

class RPCMethod(object):
    """
    Wrapped around exported methods that allows to run checks before and
    after a method is executed, without having to perform a lookup upon
    each execution.
    """

    def __init__(self, method):
        self.__method = method
        self.im_before = getattr(method.im_self, '__before__', None)
        self.im_after  = getattr(method.im_self, '__after__', None)

    def __getattr__(self, key):
        return getattr(self.__method, key)

    def __call__(self, *args, **kwargs):
        try:
            if self.im_before:
                self.im_before(self.__method)
        except Exception as e:
            log.exception(e)

        result = exc_info = None
        try:
            result = self.__method(*args, **kwargs)
        except RPCError:
            exc_info = sys.exc_info()
        except Exception as e:
            log.exception(e)
            exc_info = sys.exc_info()

        try:
            if self.im_after:
                self.im_after(self.__method)
        except Exception as e:
            log.exception(e)

        if exc_info:
            raise exc_info[1], None, exc_info[2]

        return result

class RPCServer(object):
    """

    """

    def __init__(self, socket_path=None, threaded=True):
        self.config = common.get_config()
        self.jobs = []
        self.methods = {}
        self.receivers = []
        self.running = False

    def add_receiver(self, receiver):
        """
        Adds a receiver to the RPC server.

        :param receiver: the receiver to add
        :type receiver: Receiver
        """
        receiver.set_server(self)
        self.receivers.append(receiver)

        if self.running:
            self.jobs.append(gevent.spawn(receiver.start))

    def dispatch(self, name, args=None, kwargs=None):
        """
        Dispatch a method call into the Vmail core.

        :param name: the method's name
        :type name: str
        :param args: the positional arguments for the method call
        :type args: sequence
        :param kwargs: the named arguments for the method call
        :type kwargs: dict
        """

        # Ensure that args is iterable and kwargs is a dict, so we don't
        # bugger up our method call.
        try:
            args = tuple(args)
        except TypeError:
            args = {}

        try:
            kwargs = dict(kwargs)
        except (TypeError, ValueError):
            kwargs = {}

        log.debug('calling %s(%r, %r)', name, args, kwargs)

        # Call the method
        return self.methods[name](*args, **kwargs)

    def emit(self, event):
        """
        Emits an event to the subscribed clients.

        :param event: the event to emit
        :type event: Event
        """

    def get_method_list(self):
        """
        Returns a list of the exported methods.

        :returns: the exported methods
        :rtype: list
        """
        return self.methods.keys()

    def get_object_method(self, name):
        """
        Returns a registered method.

        :param name: the name of the method
        :type name: str

        :returns: the registered method
        :rtype: method
        :raises KeyError: if `:param:name` is not registered
        """
        return self.methods[name]

    def register_object(self, obj, name=None):
        """
        Register an object to export it's rpc methods. These methods should
        be exported using the export decorator prior to registering the
        object.

        :param obj: the object to scan for exported methods
        :type obj: object
        :keyword name: the name to use for the object else the object name
        :type name: str
        """

        if not name:
            name = obj.__class__.__name__.lower()

        for d in dir(obj):
            if d[0] == '_':
                continue
            m = getattr(obj, d)
            if getattr(m, '_rpcserver_export', False):
                log.debug('Registering method: %s.%s', name, d)
                self.methods[name + '.' + d] = RPCMethod(getattr(obj, d))

    def start(self):
        """
        Start the RPC server, setup the incoming socket.
        """
        self.running = True
        self.jobs = [gevent.spawn(r.start) for r in self.receivers]

    def stop(self, force=False):
        """
        Stop the RPC server from accepting new requests.

        :keyword force: Kill all in-progress RPC requests (not recommended)
        :type force: bool
        """
        jobs = [gevent.spawn(r.stop) for r in self.receivers]
        gevent.joinall(jobs)
