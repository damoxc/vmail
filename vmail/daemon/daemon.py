#
# vmail/daemon/daemon.py
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
import grp
import pwd

from twisted.internet import reactor

from vmail.common import get_config
from vmail.daemon.core import Core
from vmail.daemon.rpcserver import RpcServer
from vmail.model import connect, rw_connect

class Daemon(object):

    def __init__(self):
        self.config = get_config()
        self.rpcserver = RpcServer()
        self.core = Core()

        if self.config['monitor']:
            from vmail.daemon.monitor import Monitor
            self.monitor = Monitor()
        else:
            self.monitor = None

        self.rpcserver.register_object(self.core)

    def start(self):
        # Get the uid and gid we want to run as
        gid = grp.getgrnam(self.config['group']).gr_gid
        uid = pwd.getpwnam(self.config['user']).pw_uid

        # Relinquish our root privileges
        os.setgid(gid)
        os.setuid(uid)

        # Start the RPC server
        self.rpcserver.start()

        # Start the monitor, if we need to
        if self.monitor:
            self.monitor.start()

        # Setup database connections
        connect()
        rw_connect()

        # Quaid, start the reactor
        reactor.run()

    def stop(self):
        if self.monitor:
            self.monitor.stop()
        self.rpcserver.stop()
        reactor.stop()
