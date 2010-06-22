#
# vmail/scripts/vchkpasswd.py
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

from vmail.client import client, reactor
from vmail.scripts.base import ScriptBase, argcount

class VChkPasswd(ScriptBase):

    script = 'vchkpasswd'
    usage  = 'Usage: %prog [options] user passwd'

    def on_connect(self, result):
        client.core.authenticate(self.args[0], self.args[1]).addCallbacks(
            self.on_auth_check,
            self.on_auth_check_err
        )

    def on_connect_err(self, error):
        reactor.stop()

    def on_auth_check(self, result):
        if result:
            self.result = 0
        reactor.stop()

    def on_auth_check_err(self, error):
        reactor.stop()

    @argcount(2)
    def run(self):
        self.result = 1
        client.connect().addCallbacks(self.on_connect, self.on_connect_err)
        reactor.run()
        return self.result
