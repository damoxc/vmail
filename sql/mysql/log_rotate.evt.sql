--
-- sql/mysql/log_rotate.evt.sql
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
--

CREATE EVENT IF NOT EXISTS log_rotate_event
	ON SCHEDULE EVERY 1 DAY
	STARTS
		TIMESTAMP(DATE_ADD(CURRENT_DATE(), INTERVAL 1 DAY), '06:00:00')
	COMMENT 'Removes old records from the audit archive tables'
	DO CALL log_rotate();
