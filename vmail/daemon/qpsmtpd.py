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
    def log_connection(self, remote_addr, user, relay_client, tls,
            transactions, logs):
        """
        Logs an entire connection to qpsmtpd into the database.

        :param remote_addr: The remote address connecting
        :type remote_addr: str
        :param user: The authenticated user for this connection
        :type user: str
        :param relay_client: The client is allowed to relay messages.
        :type relay_client: bool
        :param tls: Whether this was a secure connection
        :type tls: bool
        :param transactions: A list of lists containing information about
            transactions
        :type transactions: list
        :param logs: A list of lists containing log entries
        :type logs: list
        """
        log.debug('Logging connection')

        try:
            # Log the connection into the database
            connection = QpsmtpdConnection()
            connection.local_addr   = socket.getfqdn()
            connection.remote_addr  = remote_addr
            connection.user         = user
            connection.relay_client = relay_client
            connection.tls          = tls
            rw_db.add(connection)
        except Exception, e:
            log.exception(e)
            return

        # Add the log entries to the database
        self.log_entries(connection, logs)
        
        # Add the transactions to the database
        try:
            self.log_transactions(connection, transactions)
        except Exception, e:
            log.exception(e)
            return

        try:
            # Finally commit all the log information
            rw_db.commit()
        except Exception, e:
            print e

        log.debug('connection logged')
    
    def log_entries(self, connection, logs):
        """
        This method handles adding the log entries to the database.

        :param connection: The connection the logs took place in
        :type connection: QpsmtpdConnection
        :param logs: A list of lists containing the log information
        :type logs: list
        """
        log.debug('Logging log entries')

        # Add all the log entries 
        for (tnx, level, hook, plugin, message) in logs:
            log.debug('Logging entry (tnx=%s, hook=%s, plugin=%s, level=%s, message=%s', tnx, hook, plugin, level, message)
            try:
                entry = QpsmtpdLog()
                entry.transaction = tnx
                entry.hook        = hook
                entry.plugin      = plugin
                entry.level       = level
                entry.message     = message
                connection.log.append(entry)
            except Exception, e:
                log.exception(e)

    def log_transactions(self, connection, transactions):
        """
        Handle logging all the transactions where a message was sent or
        rejected within the connection.

        :param connection: The connection the logs took place in
        :type connection: QpsmtpdConnection
        :param transactions: A list of lists containing the transactions
        :type transactions: list
        """

        log.debug('Logging transactions')

        if not transactions:
            return

        # Add all the transactions
        for number, (sender, size, subject, success, message, rcpts) in enumerate(transactions):
            transaction = QpsmtpdTransaction()
            transaction.transaction = number
            transaction.sender      = sender
            transaction.size        = size
            transaction.subject     = subject
            transaction.success     = success
            transaction.message     = message
            connection.transactions.append(transaction)

            # Add the transaction recipients
            self.log_recipients(transaction, rcpts)

    def log_recipients(self, transaction, recipients):
        """
        Handle logging all the recipients that a message was sent or
        attempted to be sent to.

        :param transaction: The transaction that the recipients were used
        :type transaction: QpsmtpdTransaction
        :param recipients: list of recipient info
        :type recipients: list
        """

        log.debug('Logging recipients')

        # Add all the recipients in the transaction
        for (email_addr, success, message) in recipients:
            rcpt = QpsmtpdRecipient()
            rcpt.email_addr = email_addr
            rcpt.success = success
            rcpt.message = message
            transaction.recipients.append(rcpt)

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
