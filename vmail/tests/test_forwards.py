#
# vmail/model/procs.py
#
# Copyright (C) 2011 @UK Plc, http://www.uk-plc.net
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

from twisted.internet import reactor

from vmail.tests import test
from vmail.daemon.core import resolve_forward
from vmail.daemon.core import reverse_resolve_forward
from vmail.daemon.core import update_forwardings
from vmail.daemon.core import update_resolved_forwards

from vmail.model.classes import Forward
from vmail.model.classes import Forwards
from vmail.model.classes import ResolvedForward

class TestForwards(test.DatabaseUnitTest):

    def test_simple_resolve(self):
        forward = Forward()
        forward.domain_id = 2
        forward.source = 'contact@testing.com'
        forward.destination = 'webmaster@testing.com'
        self.db.add(forward)
        self.db.commit()

        update_resolved_forwards(self.db, forward.source)

        resolved = self.db.query(ResolvedForward
            ).filter_by(source=forward.source
            ).first()
        self.assertEqual(resolved.destination, 'fred@testing.com')

    def test_complex_resolve(self):
        forward = Forward()
        forward.domain_id = 1
        forward.source = 'contact@example.com'
        forward.destination = 'info@example.com'
        self.db.add(forward)
        self.db.commit()

        update_resolved_forwards(self.db, forward.source)

        resolved = []
        for forward in self.db.query(ResolvedForward
                ).filter_by(source=forward.source):
            resolved.append(forward.destination)

        self.assertEqual(resolved, ['dave@example.com', 'postmaster@example.com'])

    def test_delete_resolve(self):
        # Delete a forward that points at a forward
        self.db.query(Forward
            ).filter_by(source='dave@example.com'
            ).delete()

        # Resolve the remaining forwards
        update_resolved_forwards(self.db, 'dave@example.com')

        resolved = [r.destination for r in self.db.query(ResolvedForward
            ).filter_by(source='info@example.com')]
        self.assertEqual(resolved, ['dave@example.com'])

class TestForwardings(test.DatabaseUnitTest):

    def test_simple(self):
        forward = Forward()
        forward.domain_id = 2
        forward.source = 'webmaster@testing.com'
        forward.destination = 'postmaster@testing.com'
        self.db.add(forward)
        self.db.commit()

        update_forwardings(self.db, forward.source, forward.domain_id)

        forwards = self.db.query(Forwards
            ).filter_by(source=forward.source
            ).one()

        self.assertEqual(forwards.destination,
                         'fred@testing.com,postmaster@testing.com')
