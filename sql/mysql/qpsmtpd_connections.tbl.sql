--
-- sql/mysql/qpsmtpd_connections.tbl.sql
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

CREATE TABLE IF NOT EXISTS `qpsmtpd_connections` (
  `id`             int(11)      NOT NULL AUTO_INCREMENT,
  `local_addr`     varchar(80)  NOT NULL,
  `remote_addr`    varchar(80)  DEFAULT NULL,
  `user`           varchar(100) DEFAULT NULL,
  `relay_client`   tinyint(1)   DEFAULT 0,
  `tls`            tinyint(1)   DEFAULT 0,
  `date`           datetime     NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
