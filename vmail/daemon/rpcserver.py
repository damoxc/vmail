#
# vmail/daemon/main.py
#
# Copyright (C) 2010 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010 Damien Churchill <damoxc@gmail.com>
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
import stat
import logging
import traceback

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, defer

import vmail.common
from vmail.error import VmailError

log = logging.getLogger(__name__)
json = vmail.common.json

def export(func, *args, **kwargs):
    func._rpcserver_export = True
    doc = func.__doc__
    func.__doc__ = "**RPC Exported Function** \n\n"
    if doc:
        func.__doc__ += doc
    return func

class VmailProtocol(Protocol):

    __buffer =  None

    def dataReceived(self, data):
        """
        Handle receiving requests from a vmail script or another source.

        :param data: The string representation of the method call
        :type data: string
        """
        try:
            request = json.loads(data)
        except Exception, e:
            log.info("Received invalid message (%r): %s", data, e)
            return

        log.debug('request: %r', request)

        if type(request) is not dict:
            log.info('Received invalid message: type is not dict')
            return

        if 'method' not in request or 'id' not in request:
            log.info('Received invalid request: missed method or id')
            return

        request_id = request['id']
        method = request['method']
        args = request.get('args', ())
        kwargs = request.get('kwargs', {})
        reactor.callLater(0, self._dispatch, request_id, method, args,
            kwargs)

    def sendData(self, data):
        #log.debug('response: %r', data)
        self.transport.write(json.dumps(data))

    def sendResponse(self, request_id, result):
        response = {
            'id': request_id,
            'result': result,
            'error': None
        }
        self.sendData(response)

    def _dispatch(self, request_id, method, args, kwargs):
        """
        This method is run when a RPC request is made. It will run the
        local method and will send either a RPC response or RPC error
        back to the client.
        """

        def send_error():
            """
            Sends an error response with the contents of the exception
            that was raised.
            """
            exc_type, exc_value, exc_tb = sys.exc_info()

            self.sendData({
                'id': request_id,
                'result': None,
                'error': {
                    'name': exc_type.__name__,
                    'value': (exc_value.args[0] if exc_value.args else ''),
                    'traceback': ''.join(traceback.format_tb(exc_tb))
                }
            })

        if method in self.factory.methods:
            func = self.factory.methods[method]
            try:
                before = getattr(func.im_self, '__before__', None)
                if before:
                    before()
            except Exception, e:
                log.error('running __before__() failed')
                log.exception(e)

            try:
                ret = func(*args, **kwargs)
            except Exception, e:
                send_error()
                if not isinstance(e, VmailError):
                    log.exception("Exception calling %s: %s", method, e)
            else:
                if isinstance(ret, defer.Deferred):
                    pass
                else:
                    self.sendResponse(request_id, ret)

            try:
                after = getattr(func.im_self, '__after__', None)
                if after:
                    after()
            except Exception, e:
                log.error('running __after__() failed')
                log.exception(e)


class RpcServer(object):
    
    def __init__(self):
        self.factory = Factory()
        self.factory.protocol = VmailProtocol
        self.factory.methods = {}
        self.config = vmail.common.get_config()

    def register_object(self, obj, name=None):
        """
        Registers an object to export it's RPC methods. These methods should
        be exported with the export decorator prior to registering the
        object.

        :param obj: the object we want to export
        :type obj: object
        :param name: the name to use, if None, it will be the class name
        of the object
        :type name: str
        """
        if not name:
            name = obj.__class__.__name__.lower()

        for d in dir(obj):
            if d[0] == "_":
                continue
            if getattr(getattr(obj, d), '_rpcserver_export', False):
                log.debug("Registering method: %s.%s", name, d)
                self.factory.methods[name + "." + d] = getattr(obj, d)

    def start(self):
        sock_path = self.config['socket']
        if not os.path.isdir(os.path.dirname(sock_path)):
            log.fatal('Cannot create socket: directory missing')
            exit(1)

        if os.path.exists(self.config['socket']):
            log.fatal('Socket already exists')
            exit(1)

        reactor.listenUNIX(sock_path, self.factory)
        os.chmod(sock_path,
            stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO | stat.S_ISGID)
        
    def stop(self):
        reactor.stop()
        sock_path = self.config['socket']
        os.remove(sock_path)
