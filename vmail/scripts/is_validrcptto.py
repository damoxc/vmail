#
# vmail/scripts/is_validrcptto.py
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

import logging

from vmail.common import get_usage
from vmail.model import connect, db
from vmail.scripts.base import ScriptBase

log = logging.getLogger(__name__)

class IsValidRcptTo(ScriptBase):

    def run(self):
        if not self.args:
            log.error('no argument provided')
            return 1

        if '@' not in self.args[0]:
            log.error('invalid argument')
            return 1

        email = self.args[0]
        connect()
        result = db.execute('CALL is_validrcptto(:email)', {'email': email})
        row = result.fetchone()
        result.close()

        if not row:
            log.critical('is_validrcptto query failed with no result')
            return 1

        # received a > 0 returncode, so exit with it.
        if row[0]:
            return int(row[0])

        # see if we want to do some quota checking now
        if row[2] == 'local' or (row[2] == 'forward' and row[3]):
            if row[2] == 'forward':
                email = row[1]

            result = db.execute('CALL get_quotas(:email)', {'email': email})
            row = result.fetchone()
            if not row:
                # we'd rather let a message through than fail on quota
                return 0

            try:
                user_quota, domain_quota = row 
                (user, domain) = email.split('@')

                if get_usage(domain, user) >= user_quota:
                    # user is over quota, may as well stop it before maildrop
                    return 4

                if get_usage(domain) >= domain_quota:
                    # domain is over quota
                    return 5
            except Exception, e:
                log.error('error checking email %s', email)
                log.exception(e)

        return 0
