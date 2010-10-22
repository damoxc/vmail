#
# vmail/tests/test_scripts.py
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

from vmail.tests.test import BaseUnitTest

class TestScripts(BaseUnitTest):
    """
    These tests do little more than check for ImportErrors currently.
    """

    def test_base(self):
        import vmail.scripts.base

    def test_vautoreply(self):
        import vmail.scripts.vautoreply

    def test_vchkpasswd(self):
        import vmail.scripts.vchkpasswd

    def test_vchkrcptto(self):
        import vmail.scripts.vchkrcptto

    def test_vcreatemaildir(self):
        import vmail.scripts.vcreatemaildir

    def test_vdelmaildir(self):
        import vmail.scripts.vdelmaildir

    def test_vgetconfig(self):
        import vmail.scripts.vgetconfig

    def test_vgetmaildirsize(self):
        import vmail.scripts.vgetmaildirsize

    def test_vlastlogin(self):
        import vmail.scripts.vlastlogin

    def test_vlogmessage(self):
        import vmail.scripts.vlogmessage

    def test_vmaild(self):
        import vmail.scripts.vmaild

    def test_vmailman(self):
        import vmail.scripts.vmailman

    def test_vquotawarning(self):
        import vmail.scripts.vquotawarning
