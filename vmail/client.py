#
# vmail/client.py
#
# Copyright (C) 2010-2012 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2012 Damien Churchill <damoxc@gmail.com>
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
import json
import time
import logging

import gevent
from gevent import socket
from gevent.event import AsyncResult
from gevent.queue import Queue

from vmail import common

from vmail.error import ForwardNotFoundError
from vmail.error import DomainNotFoundError
from vmail.error import UserNotFoundError
from vmail.error import VmailCoreError
from vmail.error import RPCError

log = logging.getLogger(__name__)

ERRORS = {
    'ForwardNotFoundError': ForwardNotFoundError,
    'DomainNotFoundError':  DomainNotFoundError,
    'UserNotFoundError':    UserNotFoundError,
    'VmailCoreError':       VmailCoreError
}

class VmailRequest(object):

    request_id = None
    method     = None
    args       = None
    kwargs     = None

    def format_message(self):
        """
        Returns a properly formatted RPCRequest based on the properties.
        """
        return {
            'id'     : self.request_id,
            'method' : self.method,
            'params' : self.args,
            'kwargs' : self.kwargs
        }

class DottedObject(object):
    """
    This is used for dotted name calls to client
    """
    def __init__(self, client, method):
        self.client = client
        self.base = method

    def __call__(self, *args, **kwargs):
        raise Exception("You must make calls in the form of 'component.method'!")

    def __getattr__(self, name):
        return RemoteMethod(self.client, self.base + "." + name)

class RemoteMethod(DottedObject):
    """
    This is used when something like 'client.core.get_something()' is attempted.
    """
    def __call__(self, *args, **kwargs):
        return self.client(self.base, *args, **kwargs)

class Client(object):

    @property
    def socket_path(self):
        return self.__socket_path or self.__config.get('socket')

    def __init__(self, socket_path=None):
        self.__requests = {}
        self.__pending  = Queue()
        self.__buffer   = None
        self.__config   = common.get_config()
        self.__sender   = None
        self.__receiver = None
        self.__socket   = None
        self.__socket_path = socket_path
        self.__request_counter = 0

    def connect(self):
        """
        Connect to the vmaild server.
        """
        self.__socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.__socket.connect(self.socket_path)
        self.__fobj = self.__socket.makefile()

        self.__sender = gevent.spawn(self.__send)
        self.__receiver = gevent.spawn(self.__receive)

    def __send(self):
        """
        Send the RPCRequests to the server
        """
        while True:
            request = self.__pending.get()
            data = json.dumps(request.format_message())
            self.__fobj.write(data + '\n')
            self.__fobj.flush()

    def __receive(self):
        """
        Receive RPCRequests from the server
        """
        while True:
            data = self.__fobj.readline()

            if self.__buffer:
                # we have some data from the last receive() so lets
                # prepend it
                data = self.__buffer + data
                self.__buffer = None

            try:
                response = json.loads(data)
            except Exception, e:
                self.__buffer = data
                continue
            else:
                if type(response) is not dict:
                    log.debug('Received invalid response: type is not dict')
                    continue

                request_id = response.get('id')
                result = self.__requests[request_id]

                if 'error' in response and response['error'] is not None:
                    if 'name' in response['error']:
                        err_cls = ERRORS.get(response['error']['name'], RPCError)
                        result.set_exception(err_cls(response['error']['message']))
                    else:
                        result.set_exception(RPCError(response['error']))

                elif 'result' in response:
                    result.set(response['result'])

    def disconnect(self):
        """
        Disconnect the client from the vmaild server
        """
        if not self.__socket:
            return

        self.__sender.kill()
        self.__receiver.kill()
        self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()

    def __call__(self, method, *args, **kwargs):
        """
        Call a remote method.
        """
        request = VmailRequest()
        request.request_id = self.__request_counter
        self.__request_counter += 1
        request.method = method
        request.args = args
        request.kwargs = kwargs
        self.__pending.put(request)
        self.__requests[request.request_id] = result = AsyncResult()
        return result

    def __getattr__(self, method):
        return DottedObject(self, method)

class SyncClient(Client):

    def __call__(self, method, *args, **kwargs):
        return super(SyncClient, self).__call__(method, *args, **kwargs).get()

client = Client()
