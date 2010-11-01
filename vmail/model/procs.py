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
application side if needs be.
"""
import sys

from vmail.error import UserNotFoundError, VmailError
from vmail.model import *

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
    global _MODE
    if mode not in ('py', 'mysql', 'pgsql'):
        raise VmailError('Invalid procedure mode specified')
    _MODE = mode

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

def _py_get_quotas(email):
    """
    Return the domain and user quotas for the email address specified.

    :param email: The address to check
    :type email: str
    :returns: The domain and user quotas in a tuple
    :rtype: tuple
    """
    # Attempt to grab a tuple containing quotas, (user, domain)
    result = db.query(User.quota, Domain.quota
        ).join(Domain
        ).filter(User.email==email
        ).first()

    # If we have no result then raise an error
    if not result:
        raise UserNotFoundError(email)
    
    # Return if everything went okay
    return result

def _py_is_validrcptto(email):
    """
    Checks to see a recipient is valid.

    :param email: The address to check
    :type email: str
    :returns: A tuple with information about the address
    :rtype: tuple
    """
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

def _py_log_rotate():
    raise NotImplementedError('log_rotate')

def _py_process_forwards():
    raise NotImplementedError('process_forwards')

def _py_process_logins():
    raise NotImplementedError('process_logins')

def _py_resolve_forwards():
    raise NotImplementedError('resolve_forwards')

def _py_is_local():
    raise NotImplementedError('is_local')

def _mysql_get_quotas(email):
    """
    Return the domain and user quotas for the email address specified.

    :param email: The address to check
    :type email: str
    :returns: The domain and user quotas in a tuple
    :rtype: tuple
    """
    result = db.execute('CALL get_quotas(:email', {'email': email})
    row = result.fetchone()
    result.close()
    return (row[0], row[1])

def _mysql_is_validrcptto(email):
    """
    Checks to see a recipient is valid.

    :param email: The address to check
    :type email: str
    :returns: A tuple with information about the address
    :rtype: tuple
    """
    result = db.execute('CALL is_validrcptto(:email', {'email': email})
    row = result.fetchone()
    result.close()
    return (row[0], row[1], row[2])

# Create the procedure proxies
for proc in _procedures:
    setattr(_module, proc, ProcedureProxy(proc))

__all__ = _procedures + ['use_procedures']
