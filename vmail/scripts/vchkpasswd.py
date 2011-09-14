#
# vmail/scripts/vchkpasswd.py
#
# Copyright (C) 2010-2011 @UK Plc, http://www.uk-plc.net
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

from vmail.client import client
from vmail.scripts.base import DaemonScriptBase, argcount

class VChkPasswd(DaemonScriptBase):

    script = 'vchkpasswd'
    usage  = 'Usage: %prog [options] user passwd'

    @argcount(2)
    def run(self):
        try:
            self.connect()
            if client.core.authenticate(self.args[0], self.args[1]).get():
                self.log.info('%s successfully authenticated', self.args[0])
                return 0
            else:
                self.log.info('%s failed to authenticate', self.args[0])
                return 1
        except:
            self.log.error('unable to check authentication, vmaild encountered an error')
            return 1
