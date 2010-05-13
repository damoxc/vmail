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

class DBObjectProxy(ObjectProxy):

    def __getattribute__(self, key):
        if not engine:
            connect()
        return ObjectProxy.__getattribute__(self, key)

db = DBObjectProxy()
engine = ObjectProxy()

def connect():
    config = get_config()
    engine = create_engine(config['dburi'])
    init_model(engine)

def init_model(dbengine):
    global db, engine
    log.debug('Initialising the database model')
    engine._set_wrapped(dbengine)
    sm = sessionmaker(autoflush=False, autocommit=False, bind=dbengine)
    db._set_wrapped(scoped_session(sm))
