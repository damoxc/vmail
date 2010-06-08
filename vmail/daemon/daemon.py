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
import socket
import logging

import vmail.common
from vmail.scripts.base import ScriptBase

log = logging.getLogger(__name__)

class Daemon(object):
    
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX)
        self.config = vmail.common.get_config()

    def start(self):
        sock_path = self.config['socket']
        if not os.path.isdir(os.path.dirname(sock_path)):
            log.error("Could not create socket: directory doesn't exist")
            return 1
        self.sock.bind(self.config['socket'])
        self.sock.listen(2)
        self.sock.accept()
        self.stop()

    def stop(self):
        sock_path = self.config['socket']
        os.remove(sock_path)
