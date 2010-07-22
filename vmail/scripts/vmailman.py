#
# vmail/scripts/vmailman.py
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

import os
import re

from vmail.common import get_mail_dir
from vmail.model import *
from vmail.scripts.base import ScriptBase

home = '/var/mailman'
owner = 'postmaster@example.com'

class VMailMan(ScriptBase):

    def run(self):
        # renice ourselves
        os.nice(5)

        # attempt to parse the arguments
        try:
            (domain, local) = self.args[0:2]
        except:
            self.log.error('invalid arguments supplied')
            return 1
        
        # get the domain from the database
        try:
            domain = db.query(Domain).filter_by(domain=domain).one()
        except:
            self.log.error('unable to find domain')
            return 1

        # change to the mailing lists home
        maildir = get_mail_dir(domain.domain)
        os.chdir(os.path.join(maildir, '.mailman'))


