#
# vmail/client.py
#
# Copyright (C) 2010 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010 Damien Churchill <damoxc@gmail.com>
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
import logging

from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientFactory

import vmail.common

log = logging.getLogger(__name__)
json = vmail.common.json

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
            'args'   : self.args,
            'kwargs' : self.kwargs
        }

class VmailClientProtocol(Protocol):

    def connectionMade(self):
        self.__rpc_requests = {}
        self.__buffer = None
        self.factory.daemon.protocol = self
        self.factory.daemon.connect_deferred.callback(True)

    def dataReceived(self, data):
        """
        This method is called whenever we receive data from the daemon.

        :param data: a json-rpc encoded string
        """
        if self.__buffer:
            # We have some data from the last dataReceived() so lets
            # prepend it
            data = self.__buffer + data
            self.__buffer = None

        try:
            response = json.loads(data)
        except Exception, e:
            self.__buffer = data
            return

        if type(response) is not dict:
            log.debug('Received invalid response: type is not dict')
            return

        request_id = response.get('id')
        d = self.factory.daemon.pop_deferred(request_id)
        if 'error' in response and response['error'] is not None:
            d.errback(response.get('error'))
        else:
            d.callback(response.get('result'))

        del self.__rpc_requests[request_id]

    def send_request(self, request):
        """
        Sends a RPCRequest to the server.

        :param request: RPCRequest

        """
        self.__rpc_requests[request.request_id] = request
        data = json.dumps(request.format_message())
        self.transport.write(data)

class VmailClientFactory(ClientFactory):

    protocol = VmailClientProtocol

    def __init__(self, daemon):
        self.daemon = daemon

class DaemonProxy(object):

    def __init__(self):
        self.factory = VmailClientFactory(self)
        self.__request_counter = 0
        self.__deferred = {}
        self.config = vmail.common.get_config()
        self.protocol = None

    def connect(self):
        log.debug('connecting to: %s', self.config.get('socket'))
        self.socket = reactor.connectUNIX(self.config.get('socket'), 
            self.factory)
        self.connect_deferred = defer.Deferred()
        return self.connect_deferred

    def _on_connect_fail(self, result):
        self.connect_deferred.errback(False)

    def call(self, method, *args, **kwargs):
        """
        Makes a RPCRequest to the daemon.  All methods should be in the form of
        'component.method'.

        :params method: str, the method to call in the form of 'component.method'
        :params args: the arguments to call the remote method with
        :params kwargs: the keyword arguments to call the remote method with

        :return: a twisted.Deferred object that will be activated when a RPCResponse
            or RPCError is received from the daemon

        """
        # Create the VmailRequest to pass to protocol.send_request()
        request = VmailRequest()
        request.request_id = self.__request_counter
        request.method = method
        request.args = args
        request.kwargs = kwargs

        # Send the request to the server
        self.protocol.send_request(request)
        # Create a Deferred object to return and add a default errback to print
        # the error.
        d = defer.Deferred()
        d.addErrback(self.__rpc_error)

        # Store the Deferred until we receive a response from the daemon
        self.__deferred[self.__request_counter] = d

        # Increment the request counter since we don't want to use the same one
        # before a response is received.
        self.__request_counter += 1

        return d

    def pop_deferred(self, request_id):
        """
        Pops a Deferred object.  This is generally called once we receive the
        reply we were waiting on from the server.

        :param request_id: the request_id of the Deferred to pop
        :type request_id: int

        """
        return self.__deferred.pop(request_id)

    def __rpc_error(self, error_data):
        return error_data

class DottedObject(object):
    """
    This is used for dotted name calls to client
    """
    def __init__(self, daemon, method):
        self.daemon = daemon
        self.base = method

    def __call__(self, *args, **kwargs):
        raise Exception("You must make calls in the form of 'component.method'!")

    def __getattr__(self, name):
        return RemoteMethod(self.daemon, self.base + "." + name)

class RemoteMethod(DottedObject):
    """
    This is used when something like 'client.core.get_something()' is attempted.
    """
    def __call__(self, *args, **kwargs):
        return self.daemon.call(self.base, *args, **kwargs)

class Client(object):

    def __init__(self):
        self.proxy = DaemonProxy()

    def connect(self):
        return self.proxy.connect()
    
    def __getattr__(self, method):
        return DottedObject(self.proxy, method)

client = Client()
