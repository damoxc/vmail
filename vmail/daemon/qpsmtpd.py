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
    def log(self, connection_id, transaction_id, hook, plugin, level,
            message):
        """
        Log a message in a SMTP transaction to the database.

        :param connection_id: The connection to link this log entry to
        :type connection_id: int
        :param transaction_id: The transaction to link this log entry to
        :type transaction_id: int
        :param hook: The hook in which this log message was called
        :type hook: string
        :param plugin: The plugin the message originates from
        :type plugin: string
        :param level: The level of the message
        :type level: int
        :param message: The message to log
        :type message: string
        """

        try:
            entry = QpsmtpdLog()
            entry.connection_id = connection_id
            entry.transaction_id = transaction_id
            entry.hook = hook
            entry.plugin = plugin
            entry.level = level
            entry.message = message
            rw_db.add(entry)
            rw_db.commit()
        except Exception, e:
            log.exception(e)

        return None

    @export
    def log_connect(self, remote_addr):
        """
        Logs the beginning of a connection to qpsmtpd.

        :param remote_addr: The remote address connecting
        :type remote_addr: str
        """
        try:
            connection = QpsmtpdConnection()
            connection.local_addr = socket.getfqdn()
            connection.remote_addr = remote_addr
            rw_db.add(connection)
            rw_db.commit()
        except Exception, e:
            log.exception(e)
        else:
            return connection.id

    @export
    def log_post_connect(self, connection_id, user, relay_client, tls):
        """
        Updates the information on the qpsmtpd connection.

        :param connection_id: The connection to update
        :type connection_id: int
        :param user: The authenticated user for this connection
        :type user: str
        :param relay_client: The client is allowed to relay messages.
        :type relay_client: bool
        :param tls: Whether this was a secure connection
        :type tls: bool
        """

        rw_db.query(QpsmtpdConnection).filter_by(id=connection_id).update({
            QpsmtpdConnection.user:         user,
            QpsmtpdConnection.relay_client: relay_client,
            QpsmtpdConnection.tls:          tls
        })
        rw_db.commit()

    @export
    def log_recipient(self, transaction_id, email_addr, success,
            message=None):
        """
        Log a recipient as part of a transaction.

        :param transaction_id: The transaction the recipient was used in
        :type transaction_id: int
        :param email_addr: The email address of the recipient
        :type email_addr: str
        :param success: Whether or not the recipient was successful
        :type success: bool
        :param message: Any message attached to the recipient
        :type message: str
        """
        try:
            rcpt = QpsmtpdRecipient()
            rcpt.transaction_id = transaction_id
            rcpt.email_addr = email_addr
            rcpt.success = success
            rcpt.message = message
            rw_db.add(rcpt)
            rw_db.commit()
        except Exception, e:
            log.exception(e)

    @export
    def log_transaction(self, connection_id):
        """
        Log a transaction passing through the email system.

        :param connection_id: The connection the transaction is part of
        :type connection_id: int
        """

        try:
            transaction = QpsmtpdTransaction()
            transaction.connection_id = connection_id
            rw_db.add(transaction)
            rw_db.commit()
        except Exception, e:
            log.exception(e)
        else:
            return transaction.id
    
    @export
    def log_post_transaction(self, transaction_id, sender, size, subject):
        """
        Updates the information on the qpsmtpd transaction.

        :param transaction_id: The transaction to update
        :type transaction_id: int
        :param sender: The message sender
        :type sender: str
        :param size: The message size
        :type size: int
        :param subject: The message subject:
        :type subject: str
        """

        rw_db.query(QpsmtpdTransaction).filter_by(id=transaction_id).update({
            QpsmtpdTransaction.sender:  sender,
            QpsmtpdTransaction.size:    size,
            QpsmtpdTransaction.subject: subject

        })
        rw_db.commit()

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
