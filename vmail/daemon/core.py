#
# vmail/daemon/core.py
#
# Copyright (C) 2010-2012 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2013 Damien Churchill <damoxc@gmail.com>
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

from email.message import Message as MIMEMessage
from email.utils import formatdate

from vmail.common import *
from vmail.daemon.rpcserver import export
from vmail.error import *
from vmail.model import *

log = logging.getLogger(__name__)

hourly_blocks = (
    datetime.timedelta(seconds=3600),
    datetime.timedelta(seconds=7200),
    datetime.timedelta(seconds=14400),
)

daily_blocks = (
    datetime.timedelta(days=1),
    datetime.timedelta(days=2),
    datetime.timedelta(days=4),
)

def update_forwardings(db, source, domain_id=None):
    """
    This method updates the forwardings table converting the vmail
    storage format for forwards into a postfix compatible format.

    :param db: The database connection to use
    :type db: ScopedSession
    :param source: The forwards source
    :type source: str
    :keyword domain_id: The id of the domain the forward belongs to
    :type domain_id: int
    """

    # Remove the old record for this forward
    db.query(Forwards).filter_by(source=source).delete()

    # Get all the immediate destinations for this forward
    destinations = ','.join([d[0] for d in db.query(Forward.destination
        ).filter_by(source=source
        )])

    # If there are no destinations return now
    if not destinations:
        return

    if not domain_id:
        raise ValueError('domain_id cannot be None if destinations exist')

    forwardings = Forwards()
    forwardings.domain_id   = domain_id
    forwardings.source      = source
    forwardings.destination = destinations
    db.add(forwardings)
    db.commit()

def update_resolved_forwards(db, source, sources=None):
    """
    This method resolves the destination of any forwards before or
    after the source's position in the chain.

    :param db: The database connection to use
    :type db: ScopedSession
    :param source: The forwards source
    :type source: str
    """

    # Ensure we don't get ourselves into a loop
    sources = sources or []
    if source in sources:
        return

    # We need to make sure we don't resolve this forward twice.
    sources.append(source)

    # Firstly grab all the destinations for this forward
    destinations = resolve_forward(db, source)

    # Secondly remove all the previously resolved forwards for this forward
    db.query(ResolvedForward).filter_by(source=source).delete()

    # Add back the new destinations
    for destination in destinations:
        db.add(ResolvedForward(source=source, destination=destination))

    # We now need to do a reverse resolve and see which forwards point
    # to this one and update their resolved destinations.
    for forward in reverse_resolve_forward(db, source):
        if source == forward:
            continue
        update_resolved_forwards(db, forward, sources)

    # Finally we must commit all these changes to the database
    db.commit()

def resolve_forward(db, source, destinations=None):
    """
    Returns a list of the final destinations of the specified
    forward source.

    :param db: The database connection to use
    :type db: ScopedSession
    :param source: The forwards source
    :type source: str
    :keyword destinations: A list of already checked destinations, mostly
        used internally to prevent looping.
    :type sources: list
    """
    users = []

    destinations = destinations or []

    # Performing a NOT IN can be expensive if you don't need to, so
    # lets adjust the query accordingly depending on destinations.
    if destinations:
        query = db.query(Forward
            ).filter(and_(
                Forward.source == source,
                ~ Forward.destination.in_(destinations)))
    else:
        query = db.query(Forward
            ).filter(Forward.source == source)

    # Loop over the query results recursively resolving as required.
    for forward in query:
        if db.execute(User.exists(forward.destination)).scalar():
            users.append(forward.destination)

        if not db.execute(Forward.exists(forward.destination)).scalar():
            continue

        destinations.append(forward.destination)
        users += resolve_forward(db, forward.destination, destinations)

    return set(users)

def reverse_resolve_forward(db, source, sources=[]):
    """
    Returns a list of any forwards that forward to this forward.

    :param db: The database connection to use
    :type db: ScopedSession
    :param source: The forwards source
    :type source: str
    :keyword sources: A list of already checked sources, mostly used
        internally to prevent looping.
    :type sources: list
    """
    sources = sources or []

    for forward in db.query(Forward).filter_by(destination=source):
        # It's quite probable we're looping at this point
        if forward.source in sources:
            break

        sources.append(forward.source)
        reverse_resolve_forward(db, forward.source, sources)
    return sources

def limit_reached_alert(user, limit_type, limit, value):
    """
    Send out a notification when a limit is reached.

    :param user: The user who has hit the limit
    :type user: User
    :param limit_type: The type of limit that has been reached
    :type limit_type: str
    :param limit: The limit amount
    :type limit: int
    :param value: The number of messages sent
    :type value: int
    """

    name  = get_config('alerts_name')
    faddr = get_config('alerts_from')
    taddr = get_config('alerts_to')

    message = MIMEMessage()
    message.add_header('From', '"%s" <%s>' % (name, faddr))
    if isinstance(taddr, list):
        message.add_header('To', ', '.join(taddr))
    else:
        message.add_header('To', taddr)
    message.add_header('Date', formatdate())
    message.add_header('Subject', 'User %s reached sending limit' % user.email)
    message.set_payload("""Hi,

The user has reached their %s limit of sending messages. They have sent %d
messages and have a limit of %d""" % (limit_type, value, limit)
    )

    # Send the message to the local SMTP server
    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(faddr, taddr, str(message))
    smtp.close()

class Core(object):

    def __init__(self, daemon):
        self.daemon = daemon

    @export
    def authenticate(self, user, pw_clear):
        """
        Authenticate a user where PLAIN or LOGIN has been used so we have
        to check the actual password.

        :param user: The username to authenticate
        :type user: str
        :param pw_clear: The password to check
        :type pw_clear: str
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
        :type user: str
        :param pw_hash: The password hash to check
        :type pw_hash: str
        :param ticket: The msg used to generate the auth token
        :type ticket: str
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
        :type remote_addr: str
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
        :type remote_addr: str
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
    def check_limits(self, address):
        """
        Check to see whether a sender has hit their sending limits.

        :param address: The address to check
        :type address: str
        """
        address = address.lower()
        user = rw_db.query(User).filter_by(email=address).first()
        if not user:
            raise ValueError('Not a valid user')

        now  = datetime.datetime.now()

        # Check for a sending block placed on the user
        block = user.get_block(BLOCK_SENDING)
        if block and block.expires > now:
            return {'action': 'deny', 'type': 'block', 'expires': block.expires.ctime()}

        daily_limit  = user.daily_limit
        hourly_limit = user.hourly_limit

        if not daily_limit:
            daily_limit = user.domain.daily_limit or user.domain.package.daily_limit

        if not hourly_limit:
            hourly_limit = user.domain.hourly_limit or user.domain.package.hourly_limit

        hour = now - datetime.timedelta(0, 3600)
        day  = now - datetime.timedelta(1)

        # First check that the hourly limit hasn't been reached
        hourly = long(rw_db.query(func.sum(Message.recipients)
            ).filter(Message.email==address, Message.date>=hour).scalar() or 0)

        btype = None

        # Check the limits in-place on the user to check for breaches
        if hourly >= hourly_limit:
            btype = 'hourly'
            limit = hourly_limit
            value = hourly
        else:
            daily = long(rw_db.query(func.sum(Message.recipients)
                ).filter(Message.email==address, Message.date>=day).scalar() or 0)

            if daily >= daily_limit:
                btype = 'daily'
                limit = daily_limit
                value = daily

        if btype is not None:
            limit_reached_alert(user, btype, limit, value)
            if block is not None:
                if block.count == 3:
                    log.info('disabling user %s for breaching sending limit 3 times', user.email)
                    user.enabled = 0
                else:
                    block.expires = now + hourly_blocks[block.count] if btype == 'hourly' else daily_blocks[block.count]
                    block.count += 1
                    log.info('add block for user %s; expires %s; count %d', block.email, block.expires, block.count)
            else:
                block         = Block()
                block.type    = BLOCK_SENDING
                block.expires = now + hourly_blocks[0] if btype == 'hourly' else daily_blocks[0]
                block.count   = 1
                user.blocks.append(block)
                log.info('add block for user %s; expires %s; count %d', block.email, block.expires, block.count)

            # silently fail here, chances are that it's a PK collision, if
            # not the user will be disabled shortly when they try again
            try:
                rw_db.commit()
            except:
                pass

            return {'action': 'deny', 'type': btype, 'limit': limit, 'value': value}

        return {'action': 'decline'}

    @export
    def check_whitelist(self, address):
        """
        Check whether an address is listed in the whitelist.

        :param address: The address to check
        :type address: str
        :returns: True or False
        :rtype: boolean
        """
        # Avoid a pointless db hit
        if not address:
            return False

        try:
            return bool(db.query(Whitelist).get(address))
        except NoSuchColumnError:
            log.warning('NoSuchColumnError received checking whitelist for %s', address)
            return False

    @export
    def get_local_destinations(self, forward):
        """
        Gets the resolved local destinations for the specified forward.

        :param forward: The forward to check
        :type forward: str
        :returns: The resolved local destinations
        :rtype: list
        """

        # Retrieve the local destinations that a forward may resolve to
        try:
            destinations = [r[0] for r in db.query(ResolvedForward.destination
                ).filter_by(source=forward
                ).all()]
        except NoSuchColumnError:
            log.warning('NoSuchColumnError received getting local destinations for %s', forward)
            destinations = []

        # Return if there are destinations to return
        if destinations:
            return destinations

        # If there are no resolved destinations then check for a user
        if db.query(User).filter_by(email=forward).count():
            return [forward]
        else:
            return []

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
            return user.usage.bytes if user.usage else 0L
        else:
            if not isinstance(domain, (int, long)):
                dom = db.query(Domain).filter_by(domain=domain).first()
                if not dom:
                    raise DomainNotFoundError(domain)
                domain = dom.id
            return long(db.query(func.sum(UserQuota.bytes)
                ).join(User
                ).filter_by(domain_id=domain).scalar() or 0)

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
        :type email: str
        :returns: An tuple containing (result, destination, type)
        :rtype: tuple
        """
        log.debug('checking rcpt to for %s', email)
        return procs.is_validrcptto(email, db)

    @export
    def last_login(self, email, method, remote_addr=None):
        """
        Log a login made to the email system.

        :param email: The email address used to log in
        :type email: str
        :param method: The method used to log in.
        :type method: str
        :keyword remote_addr: The remote address of the log in
        :type remote_addr: str
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
    def log_message(self, email, subject, recipients):
        """
        Log the fact a message has been queued by postfix.

        :param email: The email address of the sender
        :type email: str
        :param subject: The email's subject
        :type subject: str
        :param recipients: The number of recipients the email has
        :type recipients: int
        """

        message = Message()
        message.email   = email
        message.subject = subject
        message.host    = socket.getfqdn()
        message.date    = datetime.datetime.now()
        message.recipients = recipients
        rw_db.add(message)
        rw_db.commit()

    @export
    def send_vacation(self, email, destination):
        """
        Sends a vacation message to the destination address unless they have
        already been notified.

        :param user: The email of the user to send the message for
        :type user: str
        :param destination: The email address of the remote address
        :type destination: str
        """

        user = rw_db.query(User).filter_by(email = email).first()
        if not user:
            raise UserNotFoundError(email)

        if not user.vacation:
            log.debug('User has no vacation message')
            return False

        if not user.vacation.active:
            log.debug('Vacation message is not active')
            return False

        try:
            recipient = Address.parse(destination)
        except Exception:
            return False

        # TODO: Add support for html vacation messages
        # Build up the response message here
        message = MIMEMessage()
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

        # FIXME: This is a kludgy fix to prevent unrequired error messages
        # when a vacation message is attempted to be sent to the same person
        # more than once. This should be resolved properly by allowing
        # configurable notification intervals and modifying the database
        # accordingly.
        try:
            rw_db.commit()
        except IntegrityError:
            pass

        return True

    ######################
    # Management Methods #
    ######################
    @export
    def delete_forward(self, source):
        """
        Remove a forward from the system.

        :param source: The forwards address
        :type source: str
        """
        rw_db.query(Forward).filter_by(source=source).delete()
        rw_db.commit()

        # Finally run the process forwards procedure to update the
        # other forwards tables.
        update_forwardings(rw_db, source)

        # Update the resolved forwards as well.
        update_resolved_forwards(rw_db, source)

    @export
    def delete_user(self, email):
        """
        Remove a user from the mail system.

        :param email: The users email address or user id
        :type email: str or int
        """
        if isinstance(email, (int, long)):
            user = rw_db.query(User).get(email)
        else:
            user = rw_db.query(User).filter_by(email=email).first()

        if not user:
            raise UserNotFoundError(email)

        try:
            if os.path.isdir(user.maildir):
                shutil.rmtree(user.maildir)
        except Exception, e:
            log.error('Unable to remove maildir for %s', email)
            log.exception(e)

        rw_db.delete(user)
        rw_db.commit()

    @export
    def get_domain(self, domain):
        if isinstance(domain, (int, long)):
            return db.query(Domain).get(domain)
        else:
            return db.query(Domain).filter_by(domain=domain).one()

    @export
    def get_forward(self, source):
        """
        Get the destinations for a forward from the mail system.

        :param source: The forward's source
        :type source: str
        """
        destinations = [f.destination for f in rw_db.query(Forward
            ).filter_by(source = source)]

        if not destinations:
            raise ForwardNotFoundError(source)

        return destinations

    @export
    def get_forwards(self, domain):
        """
        Return a dict of the forwards for the specified domain.

        :param domain: The domain to fetch the forwards for
        :type domain: str or int
        :keyword full: Set to True to include the destinations
        :type full: bool
        """
        if not isinstance(domain, (int, long)):
            domain_id = db.query(Domain).filter_by(domain=domain).first()
            if not domain_id:
                raise DomainNotFoundError(domain)
            domain_id = domain_id.id
        else:
            domain_id = domain

        forwards = db.query(Forward
            ).filter_by(domain_id=domain_id,
            ).order_by(Forward.source
            ).all()
        fwds = {}
        for forward in forwards:
            destinations = fwds.setdefault(forward.source, [])
            destinations.append(forward.destination)
        return fwds

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
    def save_forward(self, domain_id, source, destinations):
        """
        Save a forwards details into the database and then reflect the
        changes to the forwardings table.

        :param domain_id: The domain to associate this forward with
        :type domain_id: int
        :param source: The forward to update
        :type source: str
        :param destinations: The forwards destinations
        :type destinations: list
        """

        # If we haven't been supplied any destinations just return
        if not destinations:
            return

        # Get the domain first to check that it is one that is hosted on
        # our system.
        domain = db.query(Domain).get(domain_id)
        if not domain:
            raise DomainNotFoundError("Couldn't find domain id %d" % domain_id)

        # Double check the forward belongs to this domain.
        if not source.endswith(domain.domain):
            raise VmailCoreError('Unable to save forward for a different domain')

        # Due to the new table structure we merely delete the old forwards
        # if there are any.
        rw_db.query(Forward).filter_by(source=source).delete()

        # Add all the new forwards as specified by the destinations list
        for destination in destinations:
            forward = Forward()
            forward.domain_id = domain_id
            forward.source = source
            forward.destination = destination
            rw_db.add(forward)

        # Commit the changes to the forwards table
        rw_db.commit()

        # Finally run the process forwards procedure to update the
        # other forwards tables.
        update_forwardings(rw_db, source, domain_id)

        # Update the resolved forwards as well.
        update_resolved_forwards(rw_db, source)

        # Return the forwards source
        return source

    @export
    def save_user(self, user, params):
        if not params:
            return
        try:
            if user:
                if 'password' in params:
                    params['_cleartext'] = params['password']
                    del params['password']

                params = dict([(getattr(User, k), params[k]) for k in params])
                if isinstance(user, (int, long)):
                    rw_db.query(User).filter_by(id=user).update(params)
                else:
                    rw_db.query(User).filter_by(email=user).update(params)
                rw_db.commit()

            else:
                user = User()
                for k, v in params.iteritems():
                    setattr(user, k, v)
                rw_db.add(user)
                rw_db.commit()
                send_welcome_message(user.email)
                return user.id
        except Exception, e:
            log.exception(e)

    @export
    def save_vacation(self, vacation, params):
        """
        Save or create a vacation message.

        :param vacation: vacation id or email of the user
        :type vacation: int or str
        :param params: dictionary of the vacation parameters
        :type params: dict
        """

        # If there aren't any parameters can just return
        if not params:
            return

        # Get the email and active parameters, if there are any.
        email = params.get('email')
        active = params.get('active')

        # Convert the parameter keys into their corresponding properties on
        # the Vacation object.
        params = dict([
            (getattr(Vacation, k), params[k])
            for k in params if hasattr(Vacation, k)])

        # Attempt to save/create the vacation message
        try:
            if isinstance(vacation, (int, long)):
                rw_db.query(Vacation).filter_by(id=vacation).update(params)
            else:
                rw_db.query(Vacation).filter_by(email=vacation).update(params)

            # Remove any notifications if the active state has changed and
            # we have an email address to filter with.
            if email and active is not None:
                rw_db.query(VacationNotification).filter_by(on_vacation=email).delete()

            rw_db.commit()
        except Exception, e:
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
