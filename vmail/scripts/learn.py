#
# vmail/scripts/learn.py
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

import rfc822
import logging

from vmail.common import Address, get_msg_path, get_config, maildrop
from vmail.scripts.base import ScriptBase

log = logging.getLogger(__name__)

class Learn(ScriptBase):

    mode = None

    def run(self):
        if len(self.args) < 3:
            log.error('incorrect arguments provided')
            return 1

        (user, folder, uid) = self.args[0:3]
        (user, host) = user.split('@')

        try:
            path = get_msg_path(host, user, folder, uid)
        except:
            log.error('message does not exist')
            return 1

        fp = open(path)
        msg = rfc822.Message(fp)

        if self.mode == 'ham':
            if not msg.getheader('X-Spam-Flag'):
                log.error('message is already ham')
                return 1

        elif self.mode == 'spam':
            if msg.getheader('X-Spam-Flag'):
                log.error('message is already spam')
                return 1

        try:
            return_path = Address.parse(msg.getheader('Return-Path'))
            sender = return_path.address
        except:
            log.warning('message has no return path')
            sender = ''

        # rewind the file pointer to the beginning
        fp.seek(0)

        host = get_config().get('filterhost')

        # deliver the message to the ham mailbox
        maildrop(fp, Address('%s@%s' % (self.mode, host)), sender)

class LearnHam(Learn):

    mode = 'ham'

class LearnSpam(Learn):

    mode = 'spam'
