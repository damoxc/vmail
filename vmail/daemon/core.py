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
import shutil
import socket
import imaplib
import logging
import datetime
from email.message import Message
from email.utils import formatdate

from twisted.internet import reactor, threads

from vmail.common import *
from vmail.daemon.rpcserver import export
from vmail.error import *
from vmail.model import *

log = logging.getLogger(__name__)

class Core(object):

    def __init__(self, daemon):
        self.daemon = daemon

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

        pw_hash  = pw_hash.encode('utf8')
        ticket   = ticket.encode('utf8')
        password = user.password.encode('utf8')

        if pw_hash != hmac.new(password, ticket).hexdigest():
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
        if rw_db.query(Host).get(remote_addr):
            raise VmailCoreError('Host %s already exists' % remote_addr)

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
        host = db.query(Host
            ).filter(Host.ip_address.like('%' + remote_addr + '%')
            ).first()

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
        if user:
            email = '%s@%s' % (user, domain)
            user = db.query(User).filter_by(email=email).first()
            if not user:
                raise UserNotFoundError(email)
            return user.usage.bytes
        else:
            if not isinstance(domain, (int, long)):
                dom = db.query(Domain).filter_by(domain=domain).first()
                if not dom:
                    raise DomainNotFoundError(domain)
                domain = dom.id
            return long(db.query(func.sum(UserQuota.bytes)
                ).join(User
                ).filter_by(domain_id=domain).scalar())

    @export
    def get_quota(self, domain, user=None):
        """
        Return the quota for the specified user or domain.
        """
        if user:
            email = '%s@%s' % (user, domain)
            user = db.query(User).filter_by(email=email).first()
            if not user:
                raise UserNotFoundError(email)
            return user.quota
        else:
            dom = db.query(Domain).filter_by(domain=domain).first()
            if not dom:
                raise DomainNotFoundError(domain)
            return dom.quota

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

        log.debug(row)

        if not row:
            log.critical('is_validrcptto() call failed with no result')
            return 1

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
        # Ensure we are working with a lowercase email address
        email = email.lower()

        try:
            user = db.query(User).filter_by(email=email).first()
        except Exception as e:
            log.exception(e)
            user = None

        if user is None:
            raise UserNotFoundError(email)

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
    def send_vacation(self, user, destination):
        """
        Sends a vacation message to the destination address unless they have
        already been notified.

        :param user: The email or user_id of the user to send the message
            for
        :type user: str or int
        :param destination: The email address of the remote address
        :type destination: str
        """

        try:
            if isinstance(user, (int, long)):
                user = rw_db.query(User).get(user)
            else:
                user = rw_db.query(User).filter_by(email=user).one()
        except Exception, e:
            log.warning("Unable to find user '%s'", user)
            log.exception(e)
            return False

        if not user.vacation:
            log.warning('User has no vacation message')
            return False

        if not user.vacation.active:
            log.info('Vacation message is not active')
            return False

        recipient = Address.parse(destination)

        # Check to see if the recipient has already been notified
        if db.query(VacationNotification).filter_by(
                on_vacation = user.email,
                notified    = recipient.address).first():
            log.info('Already notified recipient')
            return False

        # TODO: Add support for html vacation messages
        # Build up the response message here
        message = Message()
        message.add_header('From', '%s <%s>' % (user.name, user.email))
        message.add_header('To', str(recipient))
        message.add_header('Date', formatdate())
        message.add_header('Subject', user.vacation.subject)
        message.set_payload(user.vacation.body.encode('utf8'))

        # Send the message to the local SMTP server
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(user.email, recipient.address, str(message))
        smtp.close()

        log.debug("Sending vacation notification to '%s' for '%s'",
            recipient.address, user.email) 

        # Store that the recipient has been notified so we don't spam them
        # with useless information.
        notification = VacationNotification()
        notification.on_vacation = user.email
        notification.notified = destination
        notification.notified_at = datetime.datetime.now()
        rw_db.add(notification)
        rw_db.commit()
        return True

    ######################
    # Management Methods #
    ######################
    @export
    def delete_forward(self, forward):
        try:
            if isinstance(forward, (int, long)):
                rw_db.query(Forwards).filter_by(id=forward).delete()
            else:
                rw_db.query(Forwards).filter_by(source=forward).delete()
            rw_db.commit()
        except Exception, e:
            log.exception(e)

    @export
    def delete_user(self, user):
        try:
            if isinstance(user, (int, long)):
                user = rw_db.query(User).get(user)
            else:
                user = rw_db.query(User).filter_by(email=user).one()
        except Exception, e:
            log.exception(e)
        else:
            try:
                if os.path.isdir(user.maildir):
                    shutil.rmtree(user.maildir)
                    if self.daemon.monitor:
                        self.daemon.monitor.remove_watch(user.maildir)

                if user.vacation:
                    rw_db.delete(user.vacation)
                rw_db.delete(user)
                rw_db.commit()
            except Exception, e:
                log.exception(e)

    @export
    def get_domain(self, domain):
        if isinstance(domain, (int, long)):
            return db.query(Domain).get(domain)
        else:
            return db.query(Domain).filter_by(domain=domain).one()

    @export
    def get_forward(self, forward):
        if isinstance(forward, (int, long)):
            fwd = rw_db.query(Forwards).get(forward)
        else:
            fwd = rw_db.query(Forwards).filter_by(source=forward).first()

        if fwd is None:
            raise ForwardNotFoundError(forward)
        return fwd

    @export
    def get_forwards(self, domain):
        return self.get_domain(domain).forwards

    @export
    def get_users(self, domain):
        return self.get_domain(domain).users

    @export
    def get_user_count(self, domain):
        if not isinstance(domain, (int, long)):
            domain = db.query(Domain).filter_by(domain=domain).one().id
        return db.query(User).filter_by(domain_id=domain).count()

    @export
    def get_user(self, user):
        if isinstance(user, (int, long)):
            email = 'user #%d' % user
            user = db.query(User).get(user)
        else:
            email = user
            user = db.query(User).filter_by(email=email).first()

        # If the user doesn't exist throw a RPC error
        if not user:
            raise UserNotFoundError(email)

        return user

    @export
    def get_vacation(self, email):
        vacation = db.query(Vacation).filter_by(email=email).first()
        if not vacation:
            raise VmailCoreError('Cannot find vacation for %s' % email)
        return vacation

    @export
    def save_forward(self, forward, params):
        if not params:
            return
        try:
            if forward:
                params = dict([(getattr(Forwards, k), params[k]) for k in params])
                if isinstance(forward, (int, long)):
                    rw_db.query(Forwards).filter_by(id=forward).update(params)
                else:
                    rw_db.query(Forwards).filter_by(source=forward).update(params)
            else:
                forward = Forwards()
                for k, v in params.iteritems():
                    setattr(forward, k, v)
                rw_db.add(forward)
            rw_db.commit()
            if isinstance(forward, Forwards):
                return forward.id
        except Exception, e:
            log.exception(e)

    @export
    def save_user(self, user, params):
        if not params:
            return
        try:
            if user:
                if 'password' in params:
                    params['_cleartext'] = params['password']
                    del params['password']

                update_quota = 'quota' in params

                params = dict([(getattr(User, k), params[k]) for k in params])
                if isinstance(user, (int, long)):
                    rw_db.query(User).filter_by(id=user).update(params)
                else:
                    rw_db.query(User).filter_by(email=user).update(params)
                rw_db.commit()

                if update_quota:
                    if isinstance(user, (int, long)):
                        u = rw_db.query(User).get(user)
                    else:
                        u = rw_db.query(User).filter_by(email=user).one()
                    threads.deferToThread(self.update_quotafile, u.maildir,
                        u.email, u.password)
            else:
                user = User()
                for k, v in params.iteritems():
                    setattr(user, k, v)
                rw_db.add(user)
                rw_db.commit()
                send_welcome_message(user.email)
                if self.daemon.monitor:
                    self.daemon.monitor.add_watch(user.maildir)
                return user.id
        except Exception, e:
            log.exception(e)

    @export
    def save_vacation(self, vacation, params):
        if not params:
            return
        try:
            params = dict([(getattr(Vacation, k), params[k]) for k in params])
            if isinstance(vacation, (int, long)):
                rw_db.query(Vacation).filter_by(id=vacation).update(params)
            else:
                rw_db.query(Vacation).filter_by(email=vacation).update(params)
            rw_db.commit()
        except Exception, e:
            log.exception(e)

    @export
    def update_quotafile(self, maildir, username, password):
        log.info('Updating quota file for %s', username)
        maildirsize = os.path.join(maildir, 'maildirsize')
        if os.path.exists(maildirsize):
            os.remove(maildirsize)
        try:
            imap = imaplib.IMAP4('localhost')
            imap.login(username, password)
            imap.getquotaroot('INBOX')
            imap.logout()
            del imap
        except Exception, e:
            log.error('Unable to update quota file for %s', username)
            log.exception(e)
    
    # Setup and tear down methods
    def __before__(self, method):
        func = method.im_func
        func.func_globals['db'] = pool.checkout()
        func.func_globals['rw_db'] = rw_pool.checkout()

    def __after__(self, method):
        func = method.im_func

        # dispose of the database connections
        pool.checkin()
        rw_pool.checkin()
