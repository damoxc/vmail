#
# vmail/error.py
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

class VmailError(Exception):
    pass

class VmailException(Exception):
    pass

class IgnoredMessageError(VmailError):
    pass

class RPCError(VmailError):
    pass

class RPCException(VmailException):
    pass

class VmailCoreError(RPCError):
    pass

class DomainNotFoundError(VmailCoreError):
    pass

class ForwardNotFoundError(VmailCoreError):
    pass

class UserNotFoundError(VmailCoreError):
    pass
