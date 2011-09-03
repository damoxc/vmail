#
# vmail/daemon/daemon.py
#
# Copyright (C) 2010 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2011 Damien Churchill <damoxc@gmail.com>
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
import grp
import pwd
import gevent
import logging

from vmail.common import get_config
from vmail.daemon.core import Core
from vmail.daemon.qpsmtpd import Qpsmtpd
from vmail.daemon.rpcserver import RPCServer, JSONReceiver
from vmail.model import connect, rw_connect

log = logging.getLogger(__name__)

class Daemon(object):

    def __init__(self):
        self.config = get_config()
        self.rpcserver = RPCServer()
        self.core = Core(self)

        self.rpcserver.add_receiver(JSONReceiver())
        self.rpcserver.register_object(self.core)
        self.rpcserver.register_object(Qpsmtpd())

        self.running = False

    def start(self):
        # Get the uid and gid we want to run as
        try:
            gid = grp.getgrnam(self.config['group']).gr_gid
        except KeyError:
            log.fatal("Cannot find group '%s'", self.config['group'])
            return 1

        try:
            uid = pwd.getpwnam(self.config['user']).pw_uid
        except KeyError:
            log.fatal("Cannot find user '%s'", self.config['user'])
            return 1

        # Relinquish our root privileges
        os.setgid(gid)
        os.setuid(uid)

        # Setup database connections
        connect()
        rw_connect()

        # Start the RPC server
        self.rpcserver.start()

        # Start this greenlet blocking
        self.running = True
        while self.running:
            gevent.sleep(0.1)

    def stop(self):
        self.running = False
        self.rpcserver.stop()
