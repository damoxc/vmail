#
# vmail/scripts/vlogmessage.py
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

from vmail.client import client, reactor
from vmail.scripts.base import DaemonScriptBase, argcount

class VLogMessage(DaemonScriptBase):
    
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

    def on_connect(self, result):
        sender = self.args[0].lower()
        remote_addr = self.args[1] if len(self.args) == 2 else None
        return client.core.log_message(sender, self.options.user,
            self.options.subject, remote_addr,
            self.options.recipients).addCallbacks(
                self.on_logged_message,
                self.on_logged_message
            )

    def on_logged_message(self, result):
        return 0

    @argcount(1)
    def run(self):
        return self.connect()
