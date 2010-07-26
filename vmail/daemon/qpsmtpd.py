#
# vmail/daemon/qpsmtpd.py
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

import time
import random
import socket
import hashlib

from vmail.common import *
from vmail.daemon.rpcserver import export
from vmail.model import *

log = logging.getLogger(__name__)

class Qpsmtpd(object):

    @export
    def log(self, transaction_id, hook, plugin, level, message):
        """
        Log a message in a SMTP transaction to the database.

        :param transaction_id: A unique id of the qpsmtpd transaction, this 
            can be None to create a new transaction_id
        :type transaction_id: str
        :param hook: The hook in which this log message was called
        :type hook: string
        :param plugin: The plugin the message originates from
        :type plugin: string
        :param level: The level of the message
        :type level: int
        :param message: The message to log
        :type message: string

        :returns: The transaction_id
        :rtype: string
        """

        # Create the transaction_id if None exists
        if transaction_id is None:
            key = '%s+%s+%s' % (socket.getfqdn(), time.time(),
                random.random())
            transaction_id = hashlib.sha1(key).hexdigest()
            log.debug('created transaction_id: %s', transaction_id)

        # Create the log entry
        try:
            entry = QpsmtpdLog()
            entry.transaction_id = transaction_id
            entry.host = socket.getfqdn()
            entry.hook = hook
            entry.plugin = plugin
            entry.level = level
            entry.message = message
            rw_db.add(entry)
            rw_db.commit()
        except Exception, e:
            log.exception(e)
            return None
        else:
            # Return the transaction id
            return transaction_id

    # Setup and tear down methods
    def __before__(self, method):
        func = method.im_func
        func.func_globals['db'] = pool.checkout()
        func.func_globals['rw_db'] = rw_pool.checkout()

    def __after__(self, method):
        func = method.im_func

        # dispose of the database connections
        func.func_globals['db'].remove()
        pool.checkin()

        func.func_globals['rw_db'].remove()
        rw_pool.checkin()
