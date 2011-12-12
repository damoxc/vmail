#
# vmail/daemon/health.py
#
# Copyright (C) 2011 @UK Plc, http://www.uk-plc.net
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

import poplib
import socket
import imaplib
import smtplib

from vmail.common import get_config
from vmail.daemon.rpcserver import export

class Health(object):

    def __before__(self, method):
        config = get_config()
        self.username = config.get('test_username')
        self.password = config.get('test_password')

    @export
    def check_imap(self):
        imap = None
        try:
            imap = imaplib.IMAP4('mail6.london.ukplc.net')
            imap.login(self.username, self.password)
            imap.select()
            assert imap.state == 'SELECTED'
        finally:
            if imap: imap.close()

    @export
    def check_pop3(self):
        pop = None
        try:
            pop = poplib.POP3('mail6.london.ukplc.net')
            pop.user(self.username)
            pop.pass_(self.password)
            assert pop.noop() == '+OK'
        finally:
            if pop: pop.quit()

    @export
    def check_smtp_public(self):
        smtp = None
        try:
            me = socket.gethostname()
            smtp = smtplib.SMTP(me)
            code, msg = smtp.mail('unknown@example.org')
            assert code == 250

            code, msg = smtp.rcpt('unknown@example.org')
            assert code == 250

        finally:
            if smtp: smtp.close()

    @export
    def check_smtp_private(self):
        smtp = None
        try:
            smtp = smtplib.SMTP('mail6.london.ukplc.net')
            code, msg = smtp.mail('unknown@example.org')
            assert code == 250

            code, msg = smtp.rcpt('unknown@example.org')
            assert code == 250
        finally:
            if smtp: smtp.close()
