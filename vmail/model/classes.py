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
        u.admin = True
        u.enabled = True

        # Add the postmaster user to the domain
        d.users.append(u)

        return d

class Forward(object):
    pass

class Greylist(object):
    pass

class Host(object):
    pass

class Login(object):
    pass

class Message(object):
    pass

class MessageRecipient(object):
    pass

class Transport(object):
    pass

class User(object):

    def __get_password(self):
        return self._cleartext

    def __set_password(self, password):
        self._cleartext = password
        salt = hashlib.md5(password).hexdigest()
        self._password = crypt.crypt(password, salt)

    password = property(__get_password, __set_password)

class Vacation(object):
    pass

class VacationNotification(object):
    pass

class Whitelist(object):
    pass

mapper(Blacklist, blacklist)
mapper(Package, packages)
mapper(Domain, domains, properties = {
    'package': relation(Package, backref='domains'),
    '_package': domains.c.package
})
mapper(Forward, forwardings, properties = {
    'domain': relation(Domain, backref='forwards')
})
mapper(Greylist, greylist)
mapper(Host, hosts)
mapper(Login, logins)
mapper(Message, messages)
mapper(MessageRecipient, message_recipients, properties = {
    'message': relation(Message, backref='recipients', uselist=False)
});
mapper(Transport, transport, properties = {
    'domain': relation(Domain, backref='transports')
})
mapper(User, users, properties = {
    'domain': relation(Domain, backref='users'),
    'logins': relation(Login, backref=backref('user', uselist=False)),
    '_password': users.c.password,
    '_cleartext': users.c.cleartext
})
mapper(Vacation, vacation, properties = {
    'user': relation(User, uselist=False, backref=backref('vacation', uselist=False))
})
mapper(VacationNotification, vacation_notification)
mapper(Whitelist, whitelist)
