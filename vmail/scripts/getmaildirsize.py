#
# vmail/scripts/getmaildirsize.py
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

from vmail.common import get_usage
from vmail.scripts.base import ScriptBase
from vmail.model import *

log = logging.getLogger(__name__)

class GetMailDirSize(ScriptBase):

    def __init__(self):
        super(GetMailDirSize, self).__init__()
        self.parser.add_option('-q', '--quota', dest='quota',
            action='store_true', help='Display the quota as well')

    def run(self):
        if not self.args:
            log.error('no argument provided')
            return 1

        if '@' in self.args[0]:
            (user, domain) = self.args[0].split('@')
            usage = get_usage(domain, user)
            if self.options.quota:
                user = db.query(User).filter_by(email=self.args[0]).one()
                quota = user.quota
        else:
            usage = get_usage(self.args[0])
            if self.options.quota:
                domain = db.query(Domain).filter_by(domain=self.args[0]).one()
                quota = domain.quota

        if self.options.quota:
            print '%d/%d' % (usage, quota)
        else:
            print '%d' % usage
