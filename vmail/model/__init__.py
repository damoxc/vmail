#
# vmail/model/__init__.py
#
# Copyright (C) 2010-2012 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2012 Damien Churchill <damoxc@gmail.com>
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
import logging

from gevent.coros import Semaphore
from gevent.local import local

from sqlalchemy import create_engine, func, text, and_, not_, or_, exists, exc

from sqlalchemy.exc import NoSuchColumnError
from sqlalchemy.orm import sessionmaker, scoped_session

from vmail.common import get_config
from vmail.error import VmailException
from vmail.model.classes import *
from vmail.model import procs

log = logging.getLogger(__name__)

class SessionPool(object):
    """
    This class is intended to allow for the model to be used in a threaded
    environment.
    """

    def __init__(self, engine, min_sessions=10, max_sessions=25):
        self.engine = engine
        sm = sessionmaker(autoflush=False, autocommit=False, bind=engine)
        self.session = scoped_session(sm)

        self.min_sessions = min_sessions
        self.max_sessions = max_sessions

        self.session_pool = []
        self.available = []
        self.checkouts = {}
        self.sessions = local()
        self.lock = Semaphore()

    def checkin(self):
        self.lock.acquire()
        try:
            session = self.sessions.session
            if session:
                session.close()
        finally:
            self.lock.release()

    def checkout(self):
        self.lock.acquire()
        try:
            session = self.sessions.session = self.session()
            return session
        finally:
            self.lock.release()

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

def _create_engine(dburi, debug=False):
    config = get_config()
    engine_args = {
        'echo': debug
    }
    if dburi.startswith('mysql'):
        engine_args['max_overflow'] = config.get('max_overflow')
        engine_args['pool_recycle'] = 1800
        engine_args['pool_size'] = config.get('pool_size')

        if not config.get('python_procs'):
            procs.use_procedures('mysql')

        if dburi.startswith('mysql+mysqlconnector'):
            dburi = str(dburi)
    else:
        procs.use_procedures('py')

    return create_engine(dburi, **engine_args)

def connect():
    config = get_config()
    dburi = config.get('rodburi', None)
    if not dburi:
        dburi = config.get('rwdburi')
    init_model(_create_engine(dburi))

def rw_connect():
    dburi = get_config().get('rwdburi')
    init_rw_model(_create_engine(dburi))

def init_model(dbengine):
    global db, engine, pool
    log.debug('Initialising the read-only database model')
    engine._set_wrapped(dbengine)
    pool._set_wrapped(SessionPool(dbengine))
    db._set_wrapped(pool.checkout())
    procs.ro_db = db

def init_rw_model(dbengine):
    global rw_db, rw_engine, rw_pool
    log.debug('Initialising the read-write database model')
    rw_engine._set_wrapped(dbengine)
    rw_pool._set_wrapped(SessionPool(dbengine))
    rw_db._set_wrapped(rw_pool.checkout())
    procs.rw_db = rw_db

engine = ObjectProxy()
db = DBObjectProxy(connect, engine)
pool = ObjectProxy()

rw_engine = ObjectProxy()
rw_db = DBObjectProxy(rw_connect, rw_engine)
rw_pool = ObjectProxy()
