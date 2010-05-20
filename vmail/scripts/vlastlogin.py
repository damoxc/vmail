#
# vmail/scripts/vlastlogin.py
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

import socket
import datetime

from vmail.model import *
from vmail.scripts.base import ScriptBase, argcount

class VLastLogin(ScriptBase):

    script = 'vlastlogin'
    usage  = 'Usage: %prog [options] user method [addr]'

    @argcount(2)
    def run(self):
        method = self.args[1].lower()
        if method not in ('imap', 'pop3', 'rcube', 'smtp'):
            log.error('incorrect method supplied')
            return 2

        user = db.query(User).filter_by(email=self.args[0]).one()

        login = Login()
        login.email = user.email
        login.user_id = user.id
        login.method = method
        login.local_addr = socket.gethostname()
        login.remote_addr = self.args[2] if len(self.args) == 3 else None
        login.date = datetime.datetime.now()
        rw_db.add(login)
        rw_db.commit()
        return 0
