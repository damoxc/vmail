#
# vmail/scripts/vgetmaildirsize.py
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

from vmail.common import fsize
from vmail.client import client, reactor
from vmail.scripts.base import DaemonScriptBase

class VGetMailDirSize(DaemonScriptBase):

    def __init__(self):
        super(VGetMailDirSize, self).__init__(add_help_option=False)
        self.parser.add_option('-q', '--quota', dest='quota',
            action='store_true', help='Display the quota as well')
        self.parser.add_option('-h', '--human-readable', dest='human',
            action='store_true', help='Display human readable figures')
        self.parser.add_option('--help', action='callback',
            callback=self.print_help, help='show this help message and exit')

    def print_help(self, *args):
        self.parser.print_help()
        exit(0)

    def on_connect(self, result):
        if self.options.quota:
            return client.core.get_quota(self.domain, self.user).addCallbacks(
                self.on_got_quota,
                self.on_got_quota_err
            )
        else:
            return client.core.get_usage(self.domain, self.user).addCallbacks(
                self.on_got_usage,
                self.on_got_usage_err
            )

    def on_got_usage(self, usage):
        if self.options.human:
            usage = fsize(usage)
            if self.options.quota:
                self.quota = fsize(self.quota)
        print ('%s/%s' % (usage, self.quota) if 
            self.options.quota else '%s' % usage)

    def on_got_usage_err(self, error):
        self.log.error('error: %s', error.value['value'])
        return 1

    def on_got_quota(self, quota):
        self.quota = quota
        return client.core.get_usage(self.domain, self.user).addCallbacks(
            self.on_got_usage,
            self.on_got_usage_err
        )

    def on_got_quota_err(self, error):
        self.log.error('error: %s', error.value['value'])
        return 1

    def run(self):
        if not self.args:
            self.log.error('no argument provided')
            return 1

        if '@' in self.args[0]:
            (self.user, self.domain) = self.args[0].split('@')
        else:
            (self.user, self.domain) = (None, self.args[0])

        if not self.domain:
            self.log.error('no argument provided')
            return 1

        return self.connect()
