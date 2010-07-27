#
# vmail/model/tables.py
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

import datetime

from sqlalchemy import MetaData, Table, Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, String, Text, Time

meta = MetaData()

blacklist = Table('blacklist', meta,
    Column('address', String(50), primary_key=True)
)

domains = Table('domains', meta,
    Column('id', Integer, primary_key=True),
    Column('login_id', Integer, default=0),
    Column('domain', String(50)),
    Column('package', String(50)),
    Column('package_id', Integer, ForeignKey('packages.id')),
    Column('quota', Integer),
    Column('account_limit', Integer),
    Column('enabled', Boolean, default=1),
)

forwardings = Table('forwardings', meta,
    Column('id', Integer, primary_key=True),
    Column('domain_id', Integer, ForeignKey('domains.id')),
    Column('source', String(80)),
    Column('destination', Text)
)

hosts = Table('hosts', meta,
    Column('ip_address', String(15), primary_key=True),
    Column('action', String(20)),
    Column('comment', String(100))
)

logins = Table('logins', meta,
    Column('id', Integer, primary_key=True),
    Column('email', String(255)),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('method', String(10)),
    Column('local_addr', String(15)),
    Column('remote_addr', String(15)),
    Column('date', DateTime)
)

messages = Table('messages', meta,
    Column('id', Integer, primary_key=True),
    Column('date', DateTime),
    Column('user', String(100)),
    Column('sender', String(100)),
    Column('subject', String(255)),
    Column('local_addr', String(50)),
    Column('remote_addr', String(50))
)

message_recipients = Table('message_recipients', meta,
    Column('message_id', Integer, ForeignKey('messages.id'), primary_key=True),
    Column('recipient', String(100), primary_key=True)
)

packages = Table('packages', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('quota', Integer(20)),
    Column('account_limit', Integer)
)

qpsmtpd_connections = Table('qpsmtpd_connections', meta,
    Column('id', Integer, primary_key=True),
    Column('local_addr', String(80)),
    Column('remote_addr', String(80)),
    Column('user', String(100)),
    Column('relay_client', Boolean, default=False),
    Column('tls', Boolean, default=False),
    Column('date', DateTime, default=datetime.datetime.now())
)

qpsmtpd_log = Table('qpsmtpd_log', meta,
    Column('id', Integer, primary_key=True),
    Column('connection_id', Integer, ForeignKey('qpsmtpd_connections.id')),
    Column('transaction_id', Integer, ForeignKey('qpsmtpd_transactions.id')),
    Column('hook', String(20)),
    Column('plugin', String(40)),
    Column('level', Integer),
    Column('message', String(255)),
    Column('date', DateTime, default=datetime.datetime.now())
)

qpsmtpd_transactions = Table('qpsmtpd_transactions', meta,
    Column('id', Integer, primary_key=True),
    Column('connection_id', Integer, ForeignKey('qpsmtpd_connections.id')),
    Column('date', DateTime, default=datetime.datetime.now()),
    Column('sender', String(100)),
    Column('size', Integer),
    Column('subject', String(255))
)

qpsmtpd_rcpts = Table('qpsmtpd_rcpts', meta,
    Column('transaction_id', Integer,
        ForeignKey('qpsmtpd_transactions.id'), primary_key=True),
    Column('email_addr', String(100), primary_key=True),
    Column('success', Boolean),
    Column('message', String(255))
)

transport = Table('transport', meta,
    Column('id', Integer, primary_key=True),
    Column('domain_id', Integer, ForeignKey('domains.id')),
    Column('source', String(128)),
    Column('transport', String(128))
)

users = Table('users', meta,
    Column('id', Integer, primary_key=True),
    Column('domain_id', Integer, ForeignKey('domains.id')),
    Column('email', String(80)),
    Column('secondary_email', String(80)),
    Column('name', String(255)),
    Column('password', String(20)),
    Column('cleartext', String(20)),
    Column('quota', Integer),
    Column('usage', Integer, default=0),
    Column('enabled', Boolean, default=True),
    Column('admin', Boolean, default=False)
)

vacation = Table('vacation', meta,
    Column('id', Integer),
    Column('email', String(255), ForeignKey('users.email'),
        primary_key=True),
    Column('subject', String(255)),
    Column('body', Text),
    Column('cache', Text),
    Column('domain', String(255)),
    Column('created', DateTime),
    Column('active', Boolean)
)

vacation_notification = Table('vacation_notification', meta,
    Column('on_vacation', String(255), primary_key=True),
    Column('notified', String(255), primary_key=True),
    Column('notified_at', Time)
)

whitelist = Table('whitelist', meta,
    Column('address', String(50), primary_key=True)
)
