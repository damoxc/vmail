#
# vmail/scripts/vlogmessage.py
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

class VLogMessage(ScriptBase):
    
    script = 'vlogmessage'
    usage  = 'Usage: %prog [options] sender [remote_addr]'

    def __init__(self):
        super(VLogMessage, self).__init__()
        self.parser.add_option('-r', '--recipient', dest='recipients',
            action='append', help='Add a recipient to the message',
            metavar='RCPT', default=[])
        self.parser.add_option('-s', '--subject', dest='subject',
            action='store', help='Set the message subject')
        self.parser.add_option('-u', '--user', dest='user',
            action='store', help='Set the user sending the message')

    @argcount(1)
    def run(self):
        sender = self.args[0].lower()

        message = Message()
        message.date = datetime.datetime.now()
        message.sender = sender
        message.user = self.options.user
        message.subject = self.options.subject
        message.local_addr = socket.gethostname()
        message.remote_addr = self.args[1] if len(self.args) == 2 else None
        rw_db.add(message)
        rw_db.commit()

        for rcpt in self.options.recipients:
            recipient = MessageRecipient()
            recipient.message_id = message.id
            recipient.recipient = rcpt
            rw_db.add(recipient)
        rw_db.commit()
