--
-- sql/mysql/process_logins.fnc.sql
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

DROP PROCEDURE IF EXISTS `mail`.`process_logins`$$
CREATE PROCEDURE `process_logins`()
BEGIN

DECLARE _date date;
DECLARE _run, _hour int DEFAULT 1;
DECLARE _limit, _start, _end datetime;

WHILE _run > 0 DO
	SET _limit = DATE_ADD(CURDATE(), INTERVAL HOUR(NOW()) HOUR);
	SELECT DATE_ADD(DATE(date), INTERVAL HOUR(date) HOUR) INTO _start FROM logins ORDER BY date LIMIT 0, 1;
	SET _end = DATE_ADD(_start, INTERVAL 1 HOUR);
	
	IF _end > _limit THEN
		SET _run = 0;
	ELSEIF (SELECT count(id) FROM logins) = 0 THEN
		SET _run = 0;
	ELSE
		SET _date = DATE(_start);
		SET _hour = HOUR(_start);

		INSERT IGNORE INTO logins_hourly (date, hour, method, count)
			SELECT
				_date, _hour, method, COUNT(id) AS `count`
			FROM logins
			WHERE
				date >= _start AND
				date <= _end
			GROUP BY method;
		
		INSERT IGNORE INTO logins_domains (date, hour, method, domain, count)
			SELECT
				_date, _hour, l.method, d.domain, count(l.id) AS `count`
			FROM
				logins l INNER JOIN
				users u ON u.id = l.user_id INNER JOIN
				domains d ON d.id = u.domain_id
			WHERE
				l.date >= _start AND
				l.date <= _end
			GROUP BY d.domain, l.method;
		
		INSERT IGNORE INTO logins_archive (date, email, user_id, method, local_addr, remote_addr)
			SELECT
				date, email, user_id, method, local_addr, remote_addr
			FROM logins
			WHERE
				date >= _start AND
				date <= _end
			ORDER BY date;
		
		DELETE FROM logins WHERE date >= _start AND date <= _end;
	END IF;
END WHILE;

-- Remove any excess caused by deleting from the MyISAM table logins
OPTIMIZE TABLE `logins`;

-- Tidy up the logins archive table
DELETE FROM logins_archive WHERE date <= DATE_SUB(NOW(), INTERVAL 1 MONTH);

END$$

DELIMITER ;
