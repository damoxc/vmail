--
-- sql/mysql/is_validrcptto.fnc.sql
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

DROP PROCEDURE `is_validrcptto`$$
CREATE PROCEDURE `is_validrcptto`(
	_email VARCHAR(255)
)
BEGIN

DECLARE does_exist INT DEFAULT 0;
DECLARE match_id INT DEFAULT 0;
DECLARE user_enabled INT DEFAULT 0;
DECLARE domain VARCHAR(50);
DECLARE dest VARCHAR(255);

SET _email = _email;

single_loop: LOOP

	SELECT COUNT(id) INTO does_exist FROM users WHERE email = _email;

	IF does_exist > 0 THEN
		SELECT id, enabled INTO match_id, user_enabled FROM users WHERE email = _email;
	END IF;

	IF match_id > 0 AND user_enabled > 0 THEN
		SELECT 0 AS 'returncode', _email AS 'destination', 'local' AS 'type';
		LEAVE single_loop;
	END IF;

	IF match_id > 0 AND user_enabled = 0 THEN
		SELECT 2 AS 'returncode', _email AS 'destination', 'local' AS 'type';
		LEAVE single_loop;
	END IF;


	SELECT COUNT(id) INTO does_exist FROM forwardings WHERE source = _email;
	IF does_exist > 0 THEN
		SELECT id, destination INTO match_id, dest FROM forwardings WHERE source = _email;
	END IF;

	IF match_id > 0 THEN
		SELECT 0 AS 'returncode', dest AS 'destination', 'forward' AS 'type', is_local(dest) AS 'local';
		LEAVE single_loop;
	END IF;


	SET domain = SUBSTRING(_email, LOCATE('@', _email) + 1);


	SELECT COUNT(id) INTO does_exist FROM forwardings WHERE source = CONCAT('@', domain);
	IF does_exist > 0 THEN
		SELECT id, destination INTO match_id, dest FROM forwardings WHERE source = CONCAT('@', domain);
	END IF;

	IF match_id > 0 THEN
		
		SELECT 0 AS 'returncode', dest AS 'destination', 'forward' AS 'type', is_local(dest) AS 'local';
		LEAVE single_loop;
	END IF;


	SELECT COUNT(id) INTO does_exist FROM transport WHERE source = _email;
	IF does_exist > 0 THEN
		SELECT id, transport INTO match_id, dest FROM transport WHERE source = _email;
	END IF;

	IF match_id > 0 THEN
		SELECT 0 AS 'returncode', dest AS 'destination', 'transport' AS 'type'; 
		LEAVE single_loop;
	END IF;


	SELECT COUNT(id) INTO does_exist FROM transport WHERE source = domain;
	IF does_exist > 0 THEN
		SELECT id, transport INTO match_id, dest FROM transport WHERE source = domain;
	END IF;

	IF match_id > 0 THEN
		SELECT 0 AS 'returncode', dest AS 'destination', 'transport' AS 'type';
		LEAVE single_loop;
	END IF;


	SELECT COUNT(id) INTO does_exist FROM transport WHERE source = CONCAT('.', domain);
	IF does_exist > 0 THEN
		SELECT id, transport INTO match_id, dest FROM transport WHERE source = CONCAT('.', domain);
	END IF;

	IF match_id > 0 THEN
		SELECT 0 AS 'returncode', dest AS 'destination', 'transport' AS 'type';
		LEAVE single_loop;
	END IF;


	SELECT 1 AS 'returncode', _email AS 'destination', 'denied' AS 'type';
	LEAVE single_loop;
END LOOP;

END$$

DELIMITER ;
