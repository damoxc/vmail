--
-- sql/mysql/vacation.tbl.sql
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

CREATE TABLE `IF NOT EXISTS vacation` (
	`id`      int(11)      NOT NULL AUTO_INCREMENT,
	`email`   varchar(255) NOT NULL,
	`subject` varchar(255) NOT NULL,
	`body`    text         NOT NULL,
	`cache`   text         NOT NULL,
	`domain`  varchar(255) NOT NULL,
	`created` datetime     NOT NULL DEFAULT '0000-00-00 00:00:00',
	`active`  tinyint(1)   NOT NULL DEFAULT 1,
	PRIMARY KEY  (`id`),
	KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
