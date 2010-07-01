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

import hmac
import socket
import logging
import datetime

from vmail.common import *
from vmail.daemon.rpcserver import export
from vmail.model import *

log = logging.getLogger(__name__)

class Core(object):

    @export
    def authenticate(self, user, pw_clear):
        """
        Authenticate a user where PLAIN or LOGIN has been used so we have
        to check the actual password.

        :param user: The username to authenticate
        :type user: string
        :param pw_clear: The password to check
        :type pw_clear: string
        :returns: True or False
        :rtype: bool
        """
        user = self._authenticate(user)
        if not user:
            return False

        if user.password != pw_clear:
            return False
        
        return True
    
    @export
    def authenticate_cram(self, user, pw_hash, ticket):
        """
        Authenticate a user where CRAM-MD5 has been used so we have a
        password hash rather than the actual password.

        :param user: The username to authenticate
        :type user: string
        :param pw_hash: The password hash to check
        :type pw_hash: string
        :param ticket: The msg used to generate the auth token
        :type ticket: string
        :returns: True or False
        :rtype: bool
        """
        user = self._authenticate(user)
        if not user:
            return False

        pw_hash = pw_hash.encode('utf8')
        ticket = ticket.encode('utf8')

        if pw_hash != hmac.new(user.password, ticket).hexdigest():
            return False

        return True

    def _authenticate(self, user):
        user = db.query(User).filter_by(email=user).first()
        if not user:
            return False

        if not user.enabled:
            return False

        if not user.domain.enabled:
            return False

        return user

    @export
    def block_host(self, remote_addr):
        """
        Add a block for the specified host.

        :param remote_addr: The remote host to block
        :type remote_addr: string
        """
        host = Host()
        host.ip_address = remote_addr
        host.action = 'DENY_DISCONNECT'
        host.comment = 'Suspected spam source. Please go to\n'
        host.comment += 'http://www.ukplc.net/abous?ip=%s ' % remote_addr
        host.comment += 'for more information.'
        rw_db.add(host)
        rw_db.commit()

    @export
    def check_host(self, remote_addr):
        """
        Check whether the host is allowed to connect to the server.

        :param remote_addr: The remote address
        :type remote_addr: string
        :returns: (action, comment)
        :rtype: tuple
        """
        host = db.query(Host).filter(
            Host.ip_address.like('%' + remote_addr + '%')).first()

        if host:
            return (host.action, host.comment)
        else:
            return None

    @export
    def check_whitelist(self, address):
        """
        Check whether an address is listed in the whitelist.

        :param address: The address to check
        :type address: string
        :returns: True or False
        :rtype: boolean
        """
        return bool(db.query(Whitelist).get(address))

    @export
    def get_usage(self, domain, user=None):
        """
        Get the total quota usage for the specified domain or account.
        """
        try:
            return get_usage(domain, user)
        except Exception, e:
            log.warning('unable to check maildir for %s@%s', user, domain)
            return 0

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
    def is_validrcptto(self, email):
        """
        Check whether an email address is a valid recipient.

        :param email: The email address to check.
        :type email: string
        :returns: An integer value representing the result
        :rtype: int
        """
        log.debug('checking rcpt to for %s', email)
        try:
            result = db.execute('CALL is_validrcptto(:email)',
                {'email': email})
            row = result.fetchone()
            result.close()
        except Exception, e:
            log.error('error checking database')
            log.exception(e)
            return 255

        if not row:
            log.critical('is_validrcptto() call failed with no result')
            return 1

        # see if we want to do some quota checking now
        if row[2] == 'local' or (row[2] == 'forward' and row[3]):
            if row[2] == 'forward':
                email = row[1]

            log.debug('checking quotas for %s', email)
            result = db.execute('CALL get_quotas(:email)', {'email': email})
            row = result.fetchone()
            if not row:
                # we'd rather let a message through than fail on quota
                return 0

            try:
                (user_quota, domain_quota) = row
                (user, domain) = email.split('@')

                # Check a users quota
                try:
                    user_usage = get_usage(domain, user)
                except:
                    log.warning('unable to check User(%s) quota', email)
                else:
                    # user is over quota, stop it before deliver
                    if get_usage(domain, user) >= user_quota:
                        return 4

                try:
                    domain_usage = get_usage(domain)
                except:
                    log.warning('unable to check Domain(%s) quota', domain)
                else:
                    # domain is over quota
                    if get_usage(domain) >= domain_quota:
                        return 5

            except Exception, e:
                log.error('error checking User(%s)', email)
                log.exception(e)

        elif row[0] > 0:
            log.debug('returning %d for %s', row[0], email)
            # we have a return code greater than zero so we should return
            # it.
            return row[0]

        return 0

    @export
    def last_login(self, email, method, remote_addr=None):
        """
        Log a login made to the email system.

        :param email: The email address used to log in
        :type email: string
        :param method: The method used to log in.
        :type method: string
        :keyword remote_addr: The remote address of the log in
        :type remote_addr: string
        """
        try:
            user = db.query(User).filter_by(email=email).one()
        except:
            log.warning('[last_login] unable to get User(%s)', email)
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

    @export
    def log_message(self, sender, user, subject, remote_addr=None,
            recipients=()):
        """
        Log a message passing through the email system.

        :param sender: The person sending the message
        :type sender: string
        :param user: The user sending the message
        :type user: string
        :param subject: The message subject
        :type subject: string
        :param remote_addr: The remote address of the message
        :type remote_addr: string
        :param recipients: The recipients of the message
        :type recipients: sequence of strings
        """

        message = Message()
        message.date = datetime.datetime.now()
        message.sender = sender
        message.user = user or None
        message.subject = subject
        message.local_addr = socket.getfqdn()
        message.remote_addr = remote_addr
        rw_db.add(message)
        rw_db.commit()

        for rcpt in recipients:
            recipient = MessageRecipient()
            recipient.message_id = message.id
            recipient.recipient = rcpt
            rw_db.add(recipient)
        rw_db.commit()

    @export
    def get_domain(self, domain):
        if isinstance(domain, (int, long)):
            return db.query(Domain).get(domain)
        else:
            return db.query(Domain).filter_by(domain=domain).one()

    @export
    def get_users(self, domain):
        return self.get_domain(domain).users

    @export
    def get_user(self, user):
        if isinstance(user, (int, long)):
            return db.query(User).get(user)
        else:
            return db.query(User).filter_by(email=user).one()

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
