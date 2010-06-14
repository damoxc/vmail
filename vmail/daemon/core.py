#
# vmail/daemon/core.py
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
import logging
import datetime

from vmail.common import *
from vmail.daemon.rpcserver import export
from vmail.model import *

log = logging.getLogger(__name__)

class Core(object):

    @export
    def get_usage(self, domain, user=None):
        return get_usage(domain, user)

    @export
    def get_quota(self, domain, user=None):
        """
        Return the quota for the specified user or domain.
        """
        if user:
            email = '%s@%s' % (user, domain)
            return db.query(User).filter_by(email=email).one().quota
        else:
            return db.query(Domain).filter_by(domain=domain).one().quota

    @export
    def last_login(self, email, method, remote_addr=None):
        try:
            user = db.query(User).filter_by(email=email).one()
        except:
            log.warning('unable to get user')
            user = None

        login = Login()
        login.email = email
        login.user_id = user.id if user else -1
        login.method = method
        login.local_addr = socket.getfqdn()
        login.remote_addr = remote_addr
        login.date = datetime.datetime.now()
        rw_db.add(login)
        rw_db.commit()
        return True
