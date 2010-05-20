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

greylist = Table('greylist', meta,
    Column('remote_ip', String(15), primary_key=True),
    Column('mail_from', String(255), primary_key=True),
    Column('rcpt_to', String(255), primary_key=True),
    Column('block_expires', DateTime),
    Column('record_expires', DateTime),
    Column('blocked_count', Integer(20)),
    Column('passed_count', Integer(20)),
    Column('aborted_count', Integer(20)),
    Column('origin_type', String),
    Column('create_time', DateTime),
    Column('last_update', Time)
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
    Column('name', String(255)),
    Column('password', String(20)),
    Column('cleartext', String(20)),
    Column('quota', Integer),
    Column('enabled', Boolean),
    Column('admin', Boolean)
)

vacation = Table('vacation', meta,
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
