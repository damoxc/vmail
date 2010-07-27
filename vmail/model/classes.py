#
# vmail/model/classes.py
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

import crypt
import hashlib

from sqlalchemy import and_, join, desc, text
from sqlalchemy.orm import mapper, backref, relation

from vmail.common import get_mail_dir
from vmail.model.tables import *

class Blacklist(object):
    pass

class Package(object):
    pass

class Domain(object):
    
    @staticmethod
    def create(domain, package, password):
        """
        Provides an easy way to initially setup a domain in
        the database.

        :param domain: The domain name to create mail hosting for
        :type domain: str
        :param package: The package to use for the domain
        :type package: Package
        :param password: The password to use for postmaster
        :type password: str
        """
        # Create the domain
        d = Domain()
        d.domain = domain.lower()
        d.package = package
        d._package = package.name
        d.quota = package.quota
        d.account_limit = package.account_limit

        # Create the postmaster user
        u = User()
        u.email = 'postmaster@' + d.domain
        u.name = 'Postmaster'
        u.password = password
        u.quota = package.quota
        u.usage = 0
        u.admin = True
        u.enabled = True

        # Add the postmaster user to the domain
        d.users.append(u)

        return d

    def __json__(self):
        return {
            'id': self.id,
            'login_id': self.login_id,
            'domain': self.domain,
            'package': self._package,
            'package_id': self.package_id,
            'quota': self.quota,
            'account_limit': self.account_limit,
            'enabled': self.enabled
        }

class Forward(object):
    
    def __json__(self):
        return {
            'id': self.id,
            'source': self.source,
            'destination': self.destination
        }

class Host(object):
    
    def __json__(self):
        return {
            'ip_address': self.ip_address,
            'action': self.action,
            'comment': self.comment
        }   

class Login(object):
    
    def __json__(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'method': self.method,
            'local_addr': self.local_addr,
            'remote_addr': self.remote_addr,
            'date': self.date
        }

class Message(object):
    pass

class MessageRecipient(object):
    pass

class QpsmtpdConnection(object):
    pass

class QpsmtpdLog(object):
    pass

class QpsmtpdTransaction(object):
    pass

class QpsmtpdRecipient(object):
    pass

class Transport(object):
    pass

class User(object):

    @property
    def maildir(self):
        (user, domain) = self.email.split('@')
        return get_mail_dir(domain, user)

    def __get_password(self):
        return self._cleartext

    def __set_password(self, password):
        self._cleartext = password
        salt = hashlib.md5(password).hexdigest()
        self._password = crypt.crypt(password, salt)

    password = property(__get_password, __set_password)

    def __json__(self):
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'email': self.email,
            'secondary_email': self.secondary_email,
            'name': self.name,
            'password': self.password,
            'quota': self.quota,
            'usage': self.usage,
            'enabled': self.enabled,
            'admin': self.admin
        }

class Vacation(object):
    
    def __json__(self):
        return {
            'id': self.id,
            'email': self.email,
            'subject': self.subject,
            'body': self.body,
            'cache': self.cache,
            'domain': self.domain,
            'created': self.created,
            'active': self.active
        }

class VacationNotification(object):
    pass

class Whitelist(object):
    
    def __json__(self):
        return {
            'address': self.address
        }

mapper(Blacklist, blacklist)
mapper(Package, packages)
mapper(Domain, domains, properties = {
    'package': relation(Package, backref='domains'),
    '_package': domains.c.package
})
mapper(Forward, forwardings, properties = {
    'domain': relation(Domain,
        backref=backref('forwards', order_by=forwardings.c.source))
})
mapper(Host, hosts)
mapper(Login, logins)
mapper(Message, messages)
mapper(MessageRecipient, message_recipients, properties = {
    'message': relation(Message, backref='recipients', uselist=False)
})
mapper(QpsmtpdConnection, qpsmtpd_connections)
mapper(QpsmtpdTransaction, qpsmtpd_transactions, properties = {
    'connection': relation(QpsmtpdConnection, backref='transactions')
})
mapper(QpsmtpdRecipient, qpsmtpd_rcpts, properties = {
    'transaction': relation(QpsmtpdTransaction, backref='recipients')
})
mapper(QpsmtpdLog, qpsmtpd_log, properties = {
    'connection': relation(QpsmtpdConnection, backref='log'),
    'transaction': relation(QpsmtpdTransaction, backref='log')
})

mapper(Transport, transport, properties = {
    'domain': relation(Domain, backref='transports')
})
mapper(User, users, properties = {
    'domain': relation(Domain, backref=backref('users', order_by=users.c.email)),
    'logins': relation(Login, backref=backref('user', uselist=False)),
    '_password': users.c.password,
    '_cleartext': users.c.cleartext
})
mapper(Vacation, vacation, properties = {
    'user': relation(User, uselist=False, backref=backref('vacation', uselist=False))
})
mapper(VacationNotification, vacation_notification)
mapper(Whitelist, whitelist)
