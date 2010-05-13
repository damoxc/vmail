--
-- sql/mysql/domains.tbl.sql
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


DROP TABLE IF EXISTS `domains`;
CREATE TABLE `domains` (
	`id`            int(11)     NOT NULL auto_increment,
	`login_id`      int(11)     NOT NULL,
	`domain`        varchar(50) NOT NULL,
	`package`       varchar(10) NOT NULL,
	`package_id`    int(11)     NOT NULL,
	`quota`         int(11)     NOT NULL,
	`account_limit` int(11)     NOT NULL,
	PRIMARY KEY	(`id`),
	UNIQUE KEY `domain` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
