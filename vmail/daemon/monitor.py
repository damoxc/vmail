#
# vmail/daemon/monitor.py
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
import pyinotify

from twisted.internet.task import LoopingCall
from vmail.common import get_config

class MDSEventHandler(pyinotify.ProcessEvent):

    def process_default(self, event):
        if event.name != 'maildirsize':
            return
        print '%s: %s' % (event_name, os.path.join(event.path, event.name))


class Monitor(object):

    def __init__(self, mask=pyinotify.IN_DELETE | pyinotify.IN_CREATE |
            pyinotify.IN_MODIFY):
        self.mask = mask
        self.manager = pyinotify.WatchManager()
        self.handler = MDSEventHandler()
        self.notifier = pyinotify.Notifier(self.manager, self.handler)

    def start(self):
        """
        Start the maildir monitor running
        """
        dirs = []
        mailstore = get_config('mailstore')
        for domain in os.listdir(mailstore):
            # hidden folder
            if domain[0] == '.':
                continue

            domain = os.path.join(mailstore, domain)
            for user in os.listdir(domain):
                dirs.append(os.path.join(domain, user))
        
        self.watches = [self.manager.add_watch(d, self.mask) for d in dirs]
        self.loop = LoopingCall(self.process_events)
        self.loop.start(0.1)

    def stop(self):
        self.loop.stop()
        self.notifier.stop()

    def process_events(self):
        self.notifier.process_events()
        if self.notifier.check_events():
            self.notifier.read_events()
