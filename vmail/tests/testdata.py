from datetime import datetime

blacklist = [
    'voldemort@azkaban.com',
    'sauron@mordor.net'
]

domains = [
    ('example.com', 'Package 1', 1, 52428800, 5),
    ('testing.com', 'Package 2', 2, 104857600, 10)
]

forwardings = [
    (1, 'help@example.com', 'dave@example.com'),
    (1, 'info@example.com', 'help@example.com'),
    (2, 'webmaster@testing.com', 'fred@testing.com')
]

hosts = [
    ('97.38.123.17', 'DENY_DISCONNECT', 'Suspected spam source'),
    ('43.52.175.8', 'DENY_DISCONNECT', 'Suspected spam source'),
    ('145.231.109.164', 'DENY_DISCONNECT', 'Suspected spam source')
]

logins = [
    ('dave@example.com', 2, 'imap', 'mail.example.com', '1.2.3.4', datetime(2010, 8, 17, 9, 34, 13)),
    ('fred@testing.com', 4, 'pop3', 'mail.example.com', '5.6.7.8', datetime(2010, 8, 18, 10, 15, 48)),
]

packages = [
    ('Package 1', 52428800, 5),
    ('Package 2', 104857600, 10)
]

transport = [
    (1, '@example.co.uk', '@example.com')
]

users = [
    (1, 'postmaster@example.com', None, 'Postmaster', None, 'password', 52428800, True, True),
    (1, 'dave@example.com', None, 'Dave Smith', None, 'daisychain', 52428800, True, False),
    (2, 'postmaster@testing.com', None, 'Postmaster', None, 'password', 104857600, True, True),
    (2, 'fred@testing.com', None, 'Fred Jones', None, 'ecomdim', 104857600, True, False),
]

user_quotas = [
    ('postmaster@example.com', 1363148, 18),
    ('dave@example.com', 19293798, 147),
    ('postmaster@testing.com', 786432, 12),
    ('fred@testing.com', 81998643, 439)
]

vacation = [
    ('dave@example.com', 'Out of Office notification', 'Unfortunately I am currently out of the office however I will be back shortly.', datetime(2010, 7, 22, 15, 39, 12), 1)
]

vacation_notification = [
    ('dave@example.com', 'joe.bloggs@bigcompany.net', datetime(2010, 7, 23, 14, 22, 54))
]

whitelist = [
    'dumbledore@hogwarts.com',
    'gandalf@theshire.org'
]
