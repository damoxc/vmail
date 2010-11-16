--
-- sql/mysql/log_rotate.fnc.sql
--
-- Copyright (C) 2010 @UK Plc, http://www.uk-plc.net
--
-- Author:
--    2010 Damien Churchill <damoxc@gmail.com>
--
-- This program is free software; you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation; either version 3, or (at your option)
-- any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.    If not, write to:
--   The Free Software Foundation, Inc.,
--   51 Franklin Street, Fifth Floor
--   Boston, MA    02110-1301, USA.
--

DELIMITER $$
DROP PROCEDURE IF EXISTS `log_rotate`$$
CREATE PROCEDURE `log_rotate` ()
BEGIN

-- Rotate the tables around
CREATE TABLE `logins_archive_new` LIKE `logins_archive`;
RENAME TABLE logins_archive TO logins_archive_old, logins_archive_new TO logins_archive;

-- Copy the still valid records across
INSERT INTO `logins_archive` (date, email, user_id, method, local_addr, remote_addr)
	SELECT
		date, email, user_id, method, local_addr, remote_addr
	FROM logins_archive_old WHERE date > DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- Drop the old records
DROP TABLE `logins_archive_old`;

/**
 * Rotate the qpsmtpd_log and the qpsmtpd_log_archive
 */
CREATE TABLE `qpsmtpd_log_new` LIKE `qpsmtpd_log`;
RENAME TABLE `qpsmtpd_log` TO `qpsmtpd_log_old`, `qpsmtpd_log_new` TO `qpsmtpd_log`;

INSERT IGNORE INTO qpsmtpd_log_archive (connection_id, transaction, hook, plugin, level, message, date)
	SELECT
		connection_id, transaction, hook, plugin, level, message, date
	FROM qpsmtpd_log_old
	ORDER BY date;
DROP TABLE qpsmtpd_log_old;

CREATE TABLE `qpsmtpd_log_archive_new` LIKE `qpsmtpd_log_archive`;
RENAME TABLE `qpsmtpd_log_archive` TO `qpsmtpd_log_archive_old`, `qpsmtpd_log_archive_new` TO `qpsmtpd_log_archive`;

-- Copy the still valid records across
INSERT INTO `qpsmtpd_log_archive` (connection_id, transaction, hook, plugin, level, message, date)
    SELECT
        connection_id, transaction, hook, plugin, level, message, date
    FROM qpsmtpd_log_archive_old
	WHERE date > DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- Drop the old records
DROP TABLE `qpsmtpd_log_archive_old`;

END$$

DELIMITER ;
