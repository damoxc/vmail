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
import random
import logging

from gevent.coros import Semaphore
from gevent.local import local

from sqlalchemy import create_engine, func, text, and_, not_, or_, exists, exc

from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoSuchColumnError 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import Session

from vmail.common import get_config
from vmail.error import VmailException
from vmail.model.classes import *
from vmail.model import procs

log = logging.getLogger(__name__)

# class RoutingSession(Session):

#     def get_bind(self, mapper=None, clause=None):
#         if self._flushing:
#             return engines['master']
#         else:
#             return engines[
#                 random.choice(['slave1','slave2'])
#             ]

def _create_engine(dburi, debug=False, **engine_args):
    config = get_config()
    engine_args['echo'] = debug

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

def init_model(engine=None):
    if not engine:
        config = get_config()
        dburi = config.get('rodburi', None)
        if not dburi:
            dburi = config.get('rwdburi')
        engine = _create_engine(dburi)
    return sessionmaker(bind=engine, expire_on_commit=False)

# def rw_connect():
#     dburi = get_config().get('rwdburi')
#     init_rw_model(_create_engine(dburi))

# def init_model(dbengine):
#     global db, engine, pool
#     log.debug('Initialising the read-only database model')
#     engine._set_wrapped(dbengine)
#     pool._set_wrapped(SessionPool(dbengine))
#     db._set_wrapped(pool.checkout())
#     procs.ro_db = db

# def init_rw_model(dbengine):
#     global rw_db, rw_engine, rw_pool
#     log.debug('Initialising the read-write database model')
#     rw_engine._set_wrapped(dbengine)
#     rw_pool._set_wrapped(SessionPool(dbengine))
#     rw_db._set_wrapped(rw_pool.checkout())
#     procs.rw_db = rw_db

#engine = ObjectProxy()
#db = DBObjectProxy(connect, engine)
#pool = ObjectProxy()

#rw_engine = ObjectProxy()
#rw_db = DBObjectProxy(rw_connect, rw_engine)
#rw_pool = ObjectProxy()
