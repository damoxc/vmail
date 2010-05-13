# /etc/cron.d/vmail-smtp: crontab entries for the vmail-smtp package

HOME=/var/spool/qpsmtpd
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

*/10 * * * *   root     /usr/bin/sa-learn --ham /home/vmail/filter.example.com/ham/cur
*/10 * * * *   root     /usr/bin/sa-learn --spam /home/vmail/filter.example/spam/cur
