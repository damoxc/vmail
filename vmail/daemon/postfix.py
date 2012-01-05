#
# vmail/daemon/postfix.py
#
# Copyright (C) 2011 @UK Plc, http://www.uk-plc.net
#
# Author:
#   2011 Damien Churchill <damoxc@gmail.com>
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
import logging

from vmail.common import get_config
from vmail.daemon.rpcserver import export

log = logging.getLogger(__name__)

try:
    from vmail.daemon._postfix import QueueFile
    from vmail.daemon._postfix import valid_record_type
except ImportError:

    REC_TYPES = frozenset([
        'C', # first record, created by cleanup
        'T', # arrival time, required
        'c', # created time, optional
        'F', # full name, optional
        'I', # inspector transport
        'L', # loop filter transport
        'S', # sender, required
        'D', # delivered recipient, optional
        'R', # todo recipient, optional
        'O', # original recipient, optional
        '/', # canceled recipient, optional
        'W', # warning message time
        'A', # named attribute for extensions
        'K', # killed record

        '>', # redirect target
        'f', # cleanup processing flags
        'd', # cleanup delay upon arrival

        'M', # start message records

        'L', # long data record
        'N', # normal data record
        'w', # padding (was: deleted data)

        'X', # start extracted records

        'r', # return-receipt, from headers
        'e', # errors-to, from headers
        'P', # priority
        'p', # pointer indirection
        'V', # VERP delimiters

        '<', # DSN full/hdrs
        'i', # DSN full/hdrs
        'o', # DSN orig rcpt address
        'n', # DSN notify flags

        'm',

        'E', # terminator, required
    ])

    def valid_record_type(record_type):
        return record_type in REC_TYPES

    class QueueFile(object):

        def __init__(self, filename):
            self.filename = filename
            self.fp = open(filename, 'rb')
            self.finished = False
            self.records = []
            self.attributes = {}

        def close(self):
            """
            Close the file handle currently open for the queue file.
            """
            try:
                self.fp.close()
            except IOError:
                pass

        def next(self):
            if self.finished:
                raise StopIteration

            r, v = self._read_record()
            if r == 'E':
                self.finished = True
            elif r == 'A':
                key, value = v.split('=')
                self.attributes[key] = value

            self.records.append((r, v))
            return r, v

        def read(self):
            """
            Read all the records contained within the queue file.
            """
            while True:
                try:
                    self.next()
                except StopIteration:
                    break

        def _read_record(self):
            fp = self.fp
            record = fp.read(1)
            if record not in REC_TYPES:
                print fp.tell()
                raise Exception('Unknown record: ' + record)

            length = 0
            shift  = 0
            while True:
                len_byte = ord(fp.read(1))
                length |= (len_byte & 0177) << shift
                if (len_byte & 0200) == 0:
                    break
                shift += 7

            data = fp.read(length)
            return (record, data)

class Postfix(object):

    def __init__(self):
        self.config = get_config()

    @export
    def queue_stats(self):
        spool = self.config.get('postfix_spool')
        stats = {}
        for queue in ('deferred', 'active', 'maildrop'):
            queue_path = os.path.join(spool, queue)
            stats[queue] = len([
                m for d in
                    os.listdir(queue_path)
                    for m in os.listdir(os.path.join(queue_path, d))])
        return stats

    @export
    def queue_deferred(self):
        """
        Return information on the deferred messages contained within
        the queue.
        """
        raise NotImplementedError
