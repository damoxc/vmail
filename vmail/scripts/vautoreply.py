#
# vmail/scripts/vautoreply.py
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

import sys
import rfc822
import smtplib
from email.utils import formatdate

from vmail.common import Address, check_message
from vmail.error import IgnoredMessageError
from vmail.model import User, Vacation, connect, db
from vmail.scripts.base import ScriptBase

class VAutoreply(ScriptBase):

    #filename = '/var/self.log/vmail/vacation.self.log'

    def __init__(self):
        super(VAutoreply, self).__init__()
        self.parser.add_option('-f', '--from', dest='sender', action='store')

    def on_connect(self, result, recipient):
        user = self.options.sender
        client.core.send_vacation(user, recipient).addCallbacks(
            self.on_sent_vacation,
            self.on_err_vacation,
            (recipient,)
        )

    def on_sent_vacation(self, result, recipient):
        if not result:
            log.warning('not sending vacation message')
        else:
            log.info('sent vacation message to %s', recipient)
        reactor.stop()

    def on_err_vacation(self, failure):
        self.log.error('error: %s', error.value['value'])
        reactor.stop()

    def run(self):
        if not self.args:
            self.log.error('no argument provided')
            return 1

        message = rfc822.Message(sys.stdin)

        # Check for the presence of headers that indicate we shouldn't
        # respond to this
        try:
            check_message(message)
        except IgnoredMessageError as e:
            log.warning(e[0])
            return 0

        recipient = message.getheader('from') or self.args[0]

        client.connect().addCallback(self.on_connect, recipient)
        reactor.run()
