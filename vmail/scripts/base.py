#
# vmail/scripts/base.py
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

import sys
import logging
import optparse

LEVELS = { 
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

log = logging.getLogger(__name__)

def argcount(count):
    def deco(func):
        def wrapper(self):
            if not self.args:
                self.log.error('no arguments specified')
                return 1

            if len(self.args) < count:
                self.log.error('incorrect number of arguments specified')
                return 1

            return func(self)
        return wrapper
    return deco


class ScriptBase(object):

    filename = None
    usage = None

    def __init__(self, add_help_option=True):
        self.name = sys.argv[0]
        self.parser = optparse.OptionParser(usage=self.usage,
            add_help_option=add_help_option)
        self.parser.add_option('-L', '--loglevel', dest='loglevel',
            action='store', help='Set the log level', default='info')

    def setup_logging(self, level='INFO'):
        level = LEVELS.get(level.upper(), logging.INFO)

        logger = logging.getLogger('vmail')
        logger.setLevel(level)
        logger.propagate = 1
        logger.disabled = 0

        if self.filename:
            handler = logging.FileHandler(filename)
            formatter = logging.Formatter(
                '[%(levelname)-8s] %(asctime)s - %(message)s',
                '%a, %d %b %Y %H:%M:%S'
            )
        else:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')

        handler.setLevel(level)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    def run(self):
        return None

    @classmethod
    def main(cls):
        instance = cls()
        instance.log = logging.getLogger(instance.__class__.__module__)
        (instance.options, instance.args) = instance.parser.parse_args()
        instance.setup_logging(instance.options.loglevel)
        retval = instance.run()
        if isinstance(retval, int):
            sys.exit(retval)
