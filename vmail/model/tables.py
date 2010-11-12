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
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy import Boolean, DateTime, Integer, String, Text, Time

meta = MetaData()

blacklist = Table('blacklist', meta,
    Column('address', String(50)),
    PrimaryKeyConstraint('address')
)

domains = Table('domains', meta,
    Column('id', Integer),
    Column('login_id', Integer, default=0),
    Column('domain', String(50)),
    Column('package', String(50)),
    Column('package_id', Integer),
    Column('quota', Integer),
    Column('account_limit', Integer),
    Column('enabled', Boolean, default=1),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['package_id'], ['packages.id'])
)

forwardings = Table('forwardings', meta,
    Column('source', String(80)),
    Column('destination', Text),
    Column('domain_id', Integer),
    PrimaryKeyConstraint('source'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE')
)

forwards = Table('forwards', meta,
    Column('id', Integer),
    Column('domain_id', Integer),
    Column('source', String(80)),
    Column('destination', String(255)),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE')
)

hosts = Table('hosts', meta,
    Column('ip_address', String(15)),
    Column('action', String(20)),
    Column('comment', String(100)),
    PrimaryKeyConstraint('ip_address')
)

logins = Table('logins', meta,
    Column('id', Integer),
    Column('email', String(255)),
    Column('user_id', Integer),
    Column('method', String(10)),
    Column('local_addr', String(50)),
    Column('remote_addr', String(15)),
    Column('date', DateTime),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['user_id'], ['users.id'])
)

logins_domains = Table('logins_domains', meta,
    Column('date', DateTime),
    Column('hour', Integer),
    Column('method', String(10)),
    Column('domain', String(80)),
    Column('count', Integer),
    PrimaryKeyConstraint('date', 'hour', 'method', 'domain')
)

logins_hourly = Table('logins_hourly', meta,
    Column('date', DateTime),
    Column('hour', Integer),
    Column('method', String(10)),
    Column('count', Integer),
    PrimaryKeyConstraint('date', 'hour', 'method')
)

packages = Table('packages', meta,
    Column('id', Integer),
    Column('name', String(100)),
    Column('quota', Integer(20)),
    Column('account_limit', Integer),
    PrimaryKeyConstraint('id')
)

qpsmtpd_connections = Table('qpsmtpd_connections', meta,
    Column('id', Integer),
    Column('local_addr', String(80)),
    Column('remote_addr', String(80)),
    Column('user', String(100)),
    Column('relay_client', Boolean, default=False),
    Column('tls', Boolean, default=False),
    Column('date', DateTime, default=datetime.datetime.now),
    PrimaryKeyConstraint('id')
)

qpsmtpd_log = Table('qpsmtpd_log', meta,
    Column('id', Integer),
    Column('connection_id', Integer),
    Column('transaction', Integer),
    Column('hook', String(20)),
    Column('plugin', String(40)),
    Column('level', Integer),
    Column('message', String(255)),
    Column('date', DateTime, default=datetime.datetime.now),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['connection_id'], ['qpsmtpd_connections.id'])
)

qpsmtpd_transactions = Table('qpsmtpd_transactions', meta,
    Column('connection_id', Integer),
    Column('transaction', Integer),
    Column('date', DateTime, default=datetime.datetime.now),
    Column('sender', String(100)),
    Column('size', Integer),
    Column('subject', String(255)),
    Column('success', Boolean, default=False),
    Column('message', String(255)),
    PrimaryKeyConstraint('connection_id', 'transaction'),
    ForeignKeyConstraint(
        ['connection_id'],
        ['qpsmtpd_connections.id']
    ),
    ForeignKeyConstraint(
        ['connection_id', 'transaction'],
        ['qpsmtpd_log.connection_id', 'qpsmtpd_log.transaction']
    )
)

qpsmtpd_rcpts = Table('qpsmtpd_rcpts', meta,
    Column('connection_id', Integer),
    Column('transaction', Integer),
    Column('email_addr', String(100)),
    Column('success', Boolean),
    Column('message', String(255)),
    PrimaryKeyConstraint('connection_id', 'transaction', 'email_addr'),
    ForeignKeyConstraint(
        ['connection_id', 'transaction'],
        ['qpsmtpd_transactions.connection_id', 'qpsmtpd_transactions.transaction']
    ),
    ForeignKeyConstraint(
        ['connection_id', 'transaction'],
        ['qpsmtpd_log.connection_id', 'qpsmtpd_log.transaction']
    )
)

resolved_forwards = Table('resolved_forwards', meta,
    Column('id', Integer),
    Column('source', String(80)),
    Column('destination', String(255)),
    PrimaryKeyConstraint('id')
)

transport = Table('transport', meta,
    Column('id', Integer),
    Column('domain_id', Integer),
    Column('source', String(128)),
    Column('transport', String(128)),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE')
)

users = Table('users', meta,
    Column('id', Integer),
    Column('domain_id', Integer),
    Column('email', String(80)),
    Column('secondary_email', String(80)),
    Column('name', String(255)),
    Column('password', String(20)),
    Column('cleartext', String(20)),
    Column('quota', Integer),
    Column('enabled', Boolean, default=True),
    Column('admin', Boolean, default=False),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE')
)

user_quotas = Table('user_quotas', meta,
    Column('email', String(80)),
    Column('bytes', Integer, default=0),
    Column('messages', Integer, default=0),
    PrimaryKeyConstraint('email'),
    ForeignKeyConstraint(['email'], ['users.email'])
)

vacation = Table('vacation', meta,
    Column('id', Integer),
    Column('email', String(255)),
    Column('subject', String(255)),
    Column('body', Text),
    Column('cache', Text),
    Column('domain', String(255)),
    Column('created', DateTime),
    Column('active', Boolean),
    PrimaryKeyConstraint('id'),
    ForeignKeyConstraint(['email'], ['users.email'], ondelete='CASCADE')
)

vacation_notification = Table('vacation_notification', meta,
    Column('on_vacation', String(80)),
    Column('notified', String(150)),
    Column('notified_at', DateTime),
    PrimaryKeyConstraint('on_vacation', 'notified'),
    ForeignKeyConstraint(['on_vacation'], ['vacation.email'], ondelete='CASCADE')
)

whitelist = Table('whitelist', meta,
    Column('address', String(50)),
    PrimaryKeyConstraint('address')
)
