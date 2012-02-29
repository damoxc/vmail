#
# vmail/scripts/vquotawarning.py
#
# Copyright (C) 2010-2012 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2012 Damien Churchill <damoxc@gmail.com>
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

import smtplib
from email.utils import formatdate

from vmail.common import get_config, get_config_dir, deliver
from vmail.client import client
from vmail.scripts.base import DaemonScriptBase, argcount

class VQuotaWarning(DaemonScriptBase):

    @argcount(2)
    def run(self):
        self.user = self.args[0]
        self.usage = self.args[1]
        self.addrs = []

        self.connect()

        user = client.core.get_user(self.user).get()

        other = user.get('secondary_email')
        if other:
            self.addrs.append(other)

        domain = self.user.split('@', 1)[1]
        postmaster = client.core.get_user('postmaster@' + domain).get()

        self.addrs.append(postmaster.get('email'))
        other = postmaster.get('secondary_email')
        if other and other not in self.addrs:
            self.addrs.append(other)
        self.send_notifications()

    def send_notifications(self):
        postmaster = 'postmaster@' + get_config('defaulthost')
        user_msg = open(get_config_dir('user_quota.msg')).read()

        # Build up the params for the messages
        params  = {
            'usage': self.usage,
            'date': formatdate(),
            'to': self.user,
            'mailbox': self.user
        }

        # Build the warning for the user
        for key, value in params.iteritems():
            user_msg = user_msg.replace(':' + key, value)

        # Send the user warning
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(postmaster, self.user, user_msg)

        # If we don't have any additional addresses then stop
        if not self.addrs:
            reactor.stop()
            return

        # Get the admin warning message
        admin_msg = open(get_config_dir('admin_quota.msg')).read()

        for addr in self.addrs:
            params['to'] = addr
            msg = admin_msg

            # Build the admin message
            for key, value in params.iteritems():
                msg = msg.replace(':' + key, value)
            try:
                smtp.sendmail(postmaster, addr, msg)
            except:
                self.log.warning('Failed sending to %s', addr)

