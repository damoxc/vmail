#
# vmail/model/__init__.py
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

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from vmail.common import get_config
from vmail.model.classes import *

log = logging.getLogger(__name__)

class ObjectProxy(object):

    def __init__(self):
        object.__setattr__(self, '_wrapped', None)

    def _set_wrapped(self, obj):
        object.__setattr__(self, '_wrapped', obj)

    def __delattr__(self, key):
        return delattr(self._wrapped, key)

    def __getattr__(self, key):
        return getattr(self._wrapped, key)

    def __setattr__(self, key, value):
        return setattr(self._wrapped, key, value)

    def __nonzero__(self):
        return bool(self._wrapped)

    def __repr__(self):
        return repr(self._wrapped)

    def __str__(self):
        return str(self._wrapped)

class DBObjectProxy(ObjectProxy):

    def __init__(self, connector=None, engine=None):
        super(DBObjectProxy, self).__init__()
        object.__setattr__(self, '_connector', connector)
        object.__setattr__(self, '_engine', engine)

    def __getattribute__(self, key):
        if not object.__getattribute__(self, '_engine') and \
                object.__getattribute__(self, '_connector') and \
                key not in ('_wrapped', '_set_wrapped'):
            object.__getattribute__(self, '_connector')()
        return ObjectProxy.__getattribute__(self, key)

def connect():
    config = get_config()
    dburi = config.get('rodburi', None)
    if not dburi:
        dburi = config.get('rwdburi')
    init_model(create_engine(dburi))

def rw_connect():
    dburi = get_config().get('rwdburi')
    init_rw_model(create_engine(dburi))

def create_session(engine):
    if isinstance(engine, ObjectProxy):
        engine = engine._wrapped
    sm = sessionmaker(autoflush=False, autocommit=False, bind=engine)
    return scoped_session(sm)

def init_model(dbengine):
    global db, engine
    log.debug('Initialising the read-only database model')
    engine._set_wrapped(dbengine)
    db._set_wrapped(create_session(dbengine))

def init_rw_model(dbengine):
    global rw_db, rw_engine
    log.debug('Initialising the read-write database model')
    rw_engine._set_wrapped(dbengine)
    rw_db._set_wrapped(create_session(dbengine))

engine = ObjectProxy()
db = DBObjectProxy(connect, engine)

rw_engine = ObjectProxy()
rw_db = DBObjectProxy(rw_connect, rw_engine)
