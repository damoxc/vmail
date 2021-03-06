#!/usr/bin/env python
#
# setup.py
#
# Copyright (C) 2010-2011 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2010-2011 Damien Churchill <damoxc@gmail.com>
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

from setuptools import setup, find_packages, Extension
try:
    from Cython.Distutils import build_ext
    HAVE_CYTHON = True
    cmdclass    = {
        'build_ext': build_ext
    }
except ImportError:
    HAVE_CYTHON = False
    cmdclass    = {}

ext_modules = []

if HAVE_CYTHON:
    ext_modules.append(Extension('vmail.daemon._postfix',
                                 ['vmail/daemon/_postfix.pyx']))

setup(
    name         = 'vmail',
    version      = '0.4.901',
    author       = 'Damien Churchill',
    author_email = 'damoxc@gmail.com',

    cmdclass     = cmdclass,
    ext_modules  = ext_modules,
    packages     = find_packages(exclude=['tests', 'docs']),
    entry_points = """
    [console_scripts]
    vmaild          = vmail.scripts.vmaild:VMailD.main
    vgetmaildirsize = vmail.scripts.vgetmaildirsize:VGetMailDirSize.main
    vcreatemaildir  = vmail.scripts.vcreatemaildir:VCreateMailDir.main
    vdelmaildir     = vmail.scripts.vdelmaildir:VDelMailDir.main
    vchkrcptto      = vmail.scripts.vchkrcptto:VChkRcptTo.main
    vgetconfig      = vmail.scripts.vgetconfig:VGetConfig.main
    vautoreply      = vmail.scripts.vautoreply:VAutoreply.main
    vmailman        = vmail.scripts.vmailman:VMailMan.main
    vlastlogin      = vmail.scripts.vlastlogin:VLastLogin.main
    vlogmessage     = vmail.scripts.vlogmessage:VLogMessage.main
    vchkpasswd      = vmail.scripts.vchkpasswd:VChkPasswd.main
    vquotawarning   = vmail.scripts.vquotawarning:VQuotaWarning.main
    """
)
