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

from vmail.common import Address
from vmail.model import User, Vacation, connect, db
from vmail.scripts.base import ScriptBase

self.log = self.logging.getLogger(__name__)

class VAutoreply(ScriptBase):

    #filename = '/var/self.log/vmail/vacation.self.log'

    def __init__(self):
        super(VAutoreply, self).__init__()
        self.parser.add_option('-f', '--from', dest='sender', action='store')

    def run(self):
        if not self.args:
            self.log.error('no argument provided')
            return 1

        message = rfc822.Message(sys.stdin)

        # Check for the presence of headers that indicate we shouldn't respond to this
        if message.getheader('x-spam-flag').lower() == 'yes':
            self.log.debug('x-spam-flag: yes found; exiting')
            return 0

        if message.getheader('x-facebook-notify'):
            self.log.debug('mail from facebook, ignoring')
            return 0

        if message.getheader('precendence').lower() in ('bulk', 'list', 'junk'):
            self.log.debug('precedence is %s, exiting', message.getheader('precendence'))
            return 0

        if message.getheader('auto-submitted') and message.getheader('auto-submitted') != 'no':
            self.log.debug('Auto-Submitted found, exiting')

        # Check the from header for an address, else use the passed in address
        recipient = Address.parse(message.getheader('from') or self.args[0])

        # Connect to the database
        connect()

        sender = db.query(User).filter_by(email=self.options.sender).first()
        if not sender.vacation:
            self.log.error('no vacation message stored')
            return 1

        vacation = sender.vacation
        message = 'From: %s <%s>\r\n' % (sender.name, sender.email)
        message += 'To: %s\r\n' % recipient
        message += 'Date: %s\r\n' % formatdate()
        message += 'Subject: %s\r\n\r\n' % vacation.subject
        message += vacation.body

        smtp = smtplib.SMTP('127.0.0.1')
        smtp.sendmail(sender.email, recipient.address, message)
