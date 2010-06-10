#
# vmail/daemon/main.py
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
import stat
import select
import socket
import logging

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

import vmail.common
from vmail.scripts.base import ScriptBase

log = logging.getLogger(__name__)
json = vmail.common.json

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
        self.transport.write(json.dumps(data))

    def _dispatch(self, request_id, method, args, kwargs):
        print 'calling method %s' % method

class RpcServer(object):
    
    def __init__(self):
        self.factory = Factory()
        self.factory.protocol = VmailProtocol
        self.config = vmail.common.get_config()

    def start(self):
        sock_path = self.config['socket']
        if not os.path.isdir(os.path.dirname(sock_path)):
            log.error("Could not create socket: directory doesn't exist")
            return 1

        reactor.listenUNIX(sock_path, self.factory)
        os.chmod(sock_path,
            stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO | stat.S_ISGID)
        reactor.run()

    def stop(self):
        reactor.stop()
        sock_path = self.config['socket']
        os.remove(sock_path)
