#
# vmail/common.py
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
try:
    import json
except ImportError:
    import simplejson as json
import smtplib
import subprocess
import email.utils

MDS_RE = re.compile('\s*([\d\-\+]+)\s+([\d\-\+]+)')
MSG_SIZE_RE = re.compile(',S=(\d+)(,|:)')
ADDR_RE = re.compile('([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})', re.I)
CONFIG_DIR = '/etc/vmail'
STATE_DIR = '/var/lib/vmail'
DEFAULT_CONFIG = {
    'rwdburi': '',
    'rodburi': '',
    'user': 'vmail',
    'group': 'vmail',
    'monitor': True,
    'socket': '/var/run/vmail/vmaild.sock',
    'max_overflow': 10,
    'pool_size': 5,
    'mailstore': '/var/mail',
    'defaulthost': 'example.com',
    'filterhost': 'filter.example.com',
    'listhost': 'list.example.com',
    'autohost': 'autoreply.example.com'
}
_config = None

class VmailError(Exception):
    pass

class Address(object):

    def __init__(self, address, name=None):
        self.address = address
        self.name = name
        (self.user, self.host) = address.split('@')

    def __str__(self):
        return email.utils.formataddr((self.name, self.address))

    @staticmethod
    def parse(address):
        name, address = email.utils.parseaddr(address)
        if '@' not in address:
            raise VmailError('Unable to parse address')
        return Address(address, name)

def get_config(key=None):
    global _config
    if not _config:
        _config = DEFAULT_CONFIG.copy()
        try:
            _config.update(json.load(open(get_config_dir('vmail.cfg'))))
        except IOError:
            pass
    if key:
        return _config.get(key)
    else:
        return _config

def get_config_dir(filename=None):
    if filename:
        return os.path.join(CONFIG_DIR, filename)
    else:
        return CONFIG_DIR

def get_mail_dir(domain, user=None):
    mailstore = get_config().get('mailstore')
    if user:
        return os.path.join(mailstore, domain, user)
    else:
        return os.path.join(mailstore, domain)

def get_msg_path(domain, user, folder, uid):
    """
    Gets the filesystem path for the specified message and raises
    an error if it cannot be found.

    :param domain: The domain to use
    :param user: The user to use
    :param folder: The IMAP folder to look in
    :param uid: The message uid
    """

    if not folder.startswith('INBOX'):
        raise VmailError('Invalid folder specification')

    maildir = get_mail_dir(domain, user)
    if folder != 'INBOX':
        if '.' not in folder:
            raise VmailError('Invalid folder specification')

        parts = map(lambda x: '.' + x, folder.split('.')[1:])
        maildir = os.path.join(maildir, *parts)

    imapserver = get_config().get('imapserver')
    uid = str(uid)

    if imapserver == 'courier':
        for line in open(os.path.join(maildir, 'courierimapuiddb')):
            if not line.startswith(uid):
                continue
            filename = line.split()[-1]
            path = os.path.join(maildir, 'cur')
            for item in os.listdir(path):
                if item.startswith(filename):
                    return os.path.join(path, item)
        raise VmailError('Unable to find message')

    else:
        raise VmailError('Unsupported imap server')

def load_state_file(filename):
    path = os.path.join(STATE_DIR, filename)
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except:
            return {}
    else:
        return {}

def save_state_file(filename, state):
    return json.dump(state, open(os.path.join(STATE_DIR, filename), 'w'))

def read_maildirsize(maildir_path, with_quota=False):
    total_bytes = 0
    total_count = 0
    path = os.path.join(maildir_path, 'maildirsize')
    if not os.path.isfile(path):
        raise Exception('Cannot find maildirsize: %s',
            os.path.basename(maildir_path))
    
    if with_quota:
        fp = open(path)
        quota = fp.readline()
    else:
        fp = open(path)

    for line in fp:
        m = MDS_RE.search(line)
        if not m:
            continue
        total_bytes += int(m.group(1))
        total_count += int(m.group(2))
    fp.close()

    if with_quota:
        return (total_bytes, total_count, quota)
    else:
        return (total_bytes, total_count)

def get_usage(domain, user=None):
    if not user:
        maildir = get_mail_dir(domain)
        if not os.path.isdir(maildir):
            raise Exception('Domain does not exist')

        total_usage = 0
        for user in os.listdir(maildir):
            path = get_mail_dir(domain, user)

            # Skip users that don't have this file, it's better to get
            # an estimate.
            if not os.path.isfile(os.path.join(path, 'maildirsize')):
                continue

            try:
                total_usage += read_maildirsize(path)[0]
            except:
                log.warning('unable to read maildir for %s', user)
        return total_usage
    else:
        maildir_path = get_mail_dir(domain, user)
        if not os.path.isfile(os.path.join(maildir_path, 'maildirsize')):
            return 0
        return read_maildirsize(maildir_path)[0]

def send_welcome_message(address, smtphost=None):
    """
    Send the configured welcome message to the specified address.

    :param address: The address to send the message to.
    :type address: str
    """

    # Check to see if there is a welcome message to send
    if not os.path.isfile(get_config_dir('welcome.msg')):
        raise VmailError('Missing welcome message')

    # Build up the substitutable parameters
    params = {
        'to': address,
        'date': email.utils.formatdate()
    }

    # Read in the welcome message
    message = open(get_config_dir('welcome.msg')).read()

    # Make the subsitutions
    for key, value in params.iteritems():
        message = message.replace(':' + key, value)
    
    # Send the welcome messsage.
    smtp = smtplib.SMTP(smtphost or 'localhost')
    smtp.sendmail('postmaster@' + get_config().get('defaulthost'), address, message)

def maildrop(msg, deliver_to, sender):
    """
    Deliver the message to an address using maildrop.

    :param msg: A file-like object containing the message to deliver
    :type msg: file-like object
    :param deliver_to: The address to deliver to
    :type deliver_to: str or vmail.common.Address
    :param sender: The sender of the message
    :type sender: str or vmail.common.Address
    """

    if not isinstance(deliver_to, Address):
        deliver_to = Address(deliver_to)

    if isinstance(sender, Address):
        sender = sender.address

    p = subprocess.Popen(['maildrop', '-d', deliver_to.address,
                        '',
                        deliver_to.address,
                        deliver_to.user,
                        deliver_to.host,
                        sender], stdin=msg)
    if p.wait() > 0:
        raise VmailError('Unable to deliver message')

def deliver(msg, deliver_to, sender):
    """
    Deliver the message to an address using dovecot deliver.

    :param msg: A file-like object containing the message to deliver.
    :type msg: file-like object
    :param deliver_to: The address to deliver to
    :type deliver_to: str of vmail.common.Address
    :param sender: The sender of the message
    :type sender: str or vmail.common.Address
    """
    if not isinstance(deliver_to, Address):
        deliver_to = Address(deliver_to)

    if isinstance(sender, Address):
        sender = sender.address

    args = ['/usr/lib/dovecot/deliver', '-f', sender, '-d',
        deliver_to.address]

    p = subprocess.Popen(args, stdin=subprocess.PIPE)
    p.communicate(msg)

    if p.wait() > 0:
        raise VmailError('Unable to deliver message')

def fsize(fsize_b):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f KiB" % fsize_kb
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f MiB" % fsize_mb
    fsize_gb = fsize_mb / 1024.0
    return "%.1f GiB" % fsize_gb

def get_mailfolder_size(path):
    """
    Returns the size of the messages in a mail folder and any subfolders.

    :param path: The path to the mail folder
    :type path: string
    :returns: A tuple containing the message count and size
    :rtype: tuple
    """

    count = 0
    size  = 0

    # Count the messages in cur and new
    for store in ('cur', 'new'):
        for msg in os.listdir(os.path.join(path, store)):
            count += 1
            # Try to use the filename to get the size, fall back to os.stat
            # if not possible.
            match = MSG_SIZE_RE.search(msg)
            if match:
                size += int(match.group(1))
            else:
                size += os.stat(os.path.join(path, store, msg)).st_size

    # Check for any subfolders and count the messages in them
    for folder in os.listdir(path):
        if folder[0] != '.':
            continue
        folder_path = os.path.join(path, folder)
        if not os.path.isfile(os.path.join(folder_path, 'maildirfolder')):
            continue
        (subcount, subsize) = get_mailfolder_size(folder_path)
        count += subcount
        size += subsize

    return (count, size)

def generate_maildirsize(domain, user, quota):
    """
    Creates a new maildirsize file for the user.

    :param domain: The users domain
    :type domain: string
    :param user: The user
    :type user: string
    :param quota: The quota to give
    :type quota: int
    """
    maildir = get_mail_dir(domain, user)
    (count, size) = get_mailfolder_size(maildir)
    fp = open(os.path.join(maildir, 'maildirsize'), 'w')
    fp.write('%dS\n' % quota)
    fp.write('%d %d\n' % (size, count))
    fp.close()
