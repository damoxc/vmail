#
# vmail/model/procs.py
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

"""
This module is supposed to act as an interface to any stored procedures on
the database server, falling back to the procedure implemented in Python
using SQLAlchemy application side if needs be.

However using server side procedures will allow for a large performance
boost for the larger data processing functions.
"""
import sys
import logging

from vmail.error import UserNotFoundError, VmailError
from vmail.model import *

log = logging.getLogger(__name__)

# is_validrcptto return codes
VALID = 0
NOT_FOUND = 1
USER_DISABLED = 2
USER_OVER_QUOTA = 4
DOMAIN_OVER_QUOTA = 5

_mode = 'py'
_module = sys.modules[__name__]
_procedures = [
    'get_quotas',
    'is_local',   
    'is_validrcptto',
    'log_rotate', 
    'process_forwards',
    'process_logins',
    'resolve_forwards'
]

def use_procedures(mode):
    """
    Set the module to use the specified set of procedures

    :param mode: The desired mode
    :type mode: str
    """
    global _mode
    if mode not in ('py', 'mysql', 'pgsql'):
        raise VmailError('Invalid procedure mode specified')
    _mode = mode

    log.debug('Switching procedure mode to %s', mode)
    
    # Reflect the change in the procedures
    for procedure in _procedures:
        getattr(_module, procedure).update_mode()

class ProcedureProxy(object):
    """
    This class allows proxying of procedure calls to the various
    dbms.
    """

    def __init__(self, proc_name):
        self.proc_name = proc_name
        self.proc = None
        self.update_mode()

    def update_mode(self):
        self.proc = getattr(_module, '_%s_%s' % (_mode, self.proc_name))

    def __call__(self, *args, **kwargs):
        return self.proc(*args, **kwargs)

def _py_get_quotas(email, db=None):
    """
    Return the domain and user quotas for the email address specified.

    :param email: The address to check
    :type email: str
    :returns: The domain and user quotas in a tuple
    :rtype: tuple
    """
    if db is None:
        db = ro_db

    # Attempt to grab a tuple containing quotas, (user, domain)
    result = db.query(User.quota, Domain.quota
        ).join(Domain
        ).filter(User.email==email
        ).first()

    # If we have no result then raise an error
    if not result:
        raise UserNotFoundError(email)
    
    # Return if everything went okay, converting the values to long
    return (long(result[0]), long(result[1]))

def _py_is_validrcptto(email, db=None):
    """
    Checks to see a recipient is valid.

    :param email: The address to check
    :type email: str
    :returns: A tuple with information about the address
    :rtype: tuple
    """

    if db is None:
        db = ro_db

    # Lower the email as we only deal in lowercase
    email = email.lower()

    # Check to see if we have a user by that name
    user = db.query(User).filter_by(email=email).first()
    
    # Ensure we have a valid user
    if user:
        # Check if the user is enabled and return if not
        if not user.enabled:
            return (USER_DISABLED, email, 'local')

        # Check if the user is over quota and return if so
        if user.usage and user.usage.bytes >= user.quota:
            return (USER_OVER_QUOTA, email, 'local')

        # Get the domains quota values
        domain = db.query(func.sum(UserQuota.bytes), Domain.quota
            ).join(User, Domain
            ).filter(Domain.id == user.domain_id
            ).first()

        # Return if the domain is over quota
        if domain and domain[0] >= domain[1]:
            return (DOMAIN_OVER_QUOTA, email, 'local')

        # Return valid if we haven't failed any of the other checks
        return (VALID, email, 'local')

    # Check to see if we have a forward by that name
    forward = db.query(Forwards).filter_by(source=email).first()
    if forward:
        return (VALID, forward.destination, 'forward')

    # Get the domain
    domain = email.split('@')[1]

    # Check for a catch-all forward
    forward = db.query(Forwards).filter_by(source='@'+ domain).first()
    if forward:
        return (VALID, forward.destination, 'forward')

    # Check to see if there are any transport rules setup for this email
    transport = db.query(Transport).filter_by(source=email).first()
    if transport:
        return (VALID, transport.transport, 'transport')

    # Check to see if there are any transport rules for the domain
    transport = db.query(Transport).filter_by(source=domain).first()
    if transport:
        return (VALID, transport.transport, 'transport')

    # TODO: is this required/valid?
    # Check to see if there are any transport rules for a subsomain
    transport = db.query(Transport).filter_by(source='.' + domain).first()
    if transport:
        return (VALID, transport.transport, 'transport')

    # Unable to match anything in the system
    return (NOT_FOUND, email, 'denied')

def _py_log_rotate(db=None):

    if db is None:
        db = ro_db
    raise NotImplementedError('log_rotate')

def _py_process_forwards(db=None):
    """
    Updates the forwardings and resolved_forwards table with the new
    data available in the forwards table.
    """

    if db is None:
        db = rw_db

    # Get the forwards and their destinations
    fwds = {}
    fwds_order = []

    for forward in db.query(Forward).order_by(Forward.source):
        # Make sure the order stays the same
        if fwds.get(forward.source, None) is None:
            fwds_order.append(forward.source)

        # Store the destinations in a list
        fwd = fwds.setdefault(forward.source, {
            'destinations': [],
            'domain_id': -1
        })

        fwd['domain_id'] = forward.domain_id
        fwd['destinations'].append(forward.destination)

    # Loop over the forwards adding and updating
    for source in fwds_order:
        fwd = db.query(Forwards).filter_by(source=source).first()
        forward = fwds[source]
        if not fwd:
            fwd = Forwards()
            fwd.source = source
            fwd.destination = ','.join(forward['destinations'])
            fwd.domain_id = forward['domain_id']
            rw_db.add(fwd)
        else:
            fwd.destination = ','.join(forward['destinations'])

    # Remove all the forwards that no longer exist in the forwards table
    # from the forwardings table.
    db.query(Forwards
        ).filter(not_(exists(['NULL']
            ).where(Forward.source==Forwards.source))
        ).delete(False)

    # Commit the changes and make them live
    db.commit()

def _py_process_logins(db=None):
    raise NotImplementedError('is_local')

def _py_resolve_forwards(db=None):
    """
    The procedure that processes the forwards table resolving them to
    their local destinations to improve the performance of the is_local
    procedure.
    """

    if db is None:
        db = ro_db

    # Empty the resolved forwards table
    db.query(ResolvedForward).delete()

    processed = {}

    # Loop over the forwards resolving them all
    for forward in db.query(Forward):
        destination = _py_resolve_forward(forward, db)
        
        # This is not a local destination
        if not destination:
            continue
        
        # This is a duplicate
        if destination in processed.get(forward.source, []):
            continue

        # Add the resolved forward
        resolved = ResolvedForward()
        resolved.source = forward.source
        resolved.destination = destination
        db.add(resolved)

        # Store it for checking in the processed list
        destinations = processed.setdefault(forward.source, [])
        destinations.append(destination)

    db.commit()

def _py_resolve_forward(forward, db=None):
    """
    This handles resolving individual forwards within the system. This
    method is not geared for speed, a lazy implementation at best.
    """
    if db.query(User).filter_by(email=forward.destination).count():
        return forward.destination

    f2 = db.query(Forward).filter_by(source=forward.destination).first()
    if f2:
        return _py_resolve_forward(f2, db)

def _py_is_local(db=None):
    raise NotImplementedError('is_local')

def _mysql_get_quotas(email, db=None):
    """
    Return the domain and user quotas for the email address specified.

    :param email: The address to check
    :type email: str
    :returns: The domain and user quotas in a tuple
    :rtype: tuple
    """
    if db is None:
        db = ro_db

    result = db.execute('CALL get_quotas(:email)', {'email': email})
    row = result.fetchone()
    result.close()
    return (row[0], row[1])

def _mysql_is_local(email, db=None):
    """
    Check if the specified email is local.

    :param email: The email to check
    :type email: str
    """
    if db is None:
        db = ro_db

    result = db.execute('SELECT is_local(:email)', {'email': email})
    row = result.fetchone()
    result.close()
    return bool(row[0])


def _mysql_is_validrcptto(email, db=None):
    """
    Checks to see a recipient is valid.

    :param email: The address to check
    :type email: str
    :returns: A tuple with information about the address
    :rtype: tuple
    """
    if db is None:
        db = ro_db

    result = db.execute('CALL is_validrcptto(:email)', {'email': email})
    row = result.fetchone()
    result.close()
    return (row[0], row[1], row[2])

def _mysql_log_rotate(db=None):

    if db is None:
        db = rw_db
    return db.execute('CALL log_rotate()').close()

def _mysql_process_forwards(db=None):
    """
    Updates the forwardings and resolved_forwards table with the new
    data available in the forwards table.
    """
    if db is None:
        db = rw_db
    return db.execute('CALL process_forwards()').close()

def _mysql_process_logins(db=None):
    if db is None:
        db = rw_db
    return db.execute('CALL process_logins()').close()

def _mysql_resolve_forwards(db=None):
    """
    The procedure that processes the forwards table resolving them to
    their local destinations to improve the performance of the is_local
    procedure.
    """
    if db is None:
        db = rw_db
    return db.execute('CALL resolve_forwards()').close()

# Create the procedure proxies
for proc in _procedures:
    setattr(_module, proc, ProcedureProxy(proc))

__all__ = _procedures + ['use_procedures']
