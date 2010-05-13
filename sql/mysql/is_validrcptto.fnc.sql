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

DROP FUNCTION IF EXISTS `is_validrcptto`$$
CREATE FUNCTION `is_validrcptto`(
	_email VARCHAR(255)
) RETURNS int(11)
BEGIN

/* Declare the user_id variable */
DECLARE does_exist INT;
DECLARE match_id INT;
DECLARE user_enabled INT;
DECLARE domain VARCHAR(50);

SET does_exist = 0;
SET match_id = 0;
SET user_enabled = 0;
SET _email = lower(_email);

/* Check to see if we have a user */
SELECT COUNT(id) INTO does_exist FROM users WHERE lower(email) = _email;

/* Only get the user_id and user_enabled if the user exists */
IF does_exist > 0 THEN
	SELECT id, enabled INTO match_id, user_enabled FROM users WHERE lower(email) = _email;
END IF;

IF match_id > 0 AND user_enabled > 0 THEN
	RETURN 0; -- Valid user
ELSEIF match_id > 0 AND user_enabled = 0 THEN
	RETURN 2; -- Account disabled
END IF;

/* Check for an exact forward match */
SELECT COUNT(id) INTO does_exist FROM forwardings WHERE lower(source) = _email;
IF does_exist > 0 THEN
	SELECT id INTO match_id FROM forwardings WHERE lower(source) = _email;
END IF;

IF match_id > 0 THEN
	RETURN 0; -- Valid forward
END IF;

/* Get the domain part of the email address */
SET domain = SUBSTRING(_email, LOCATE('@', _email) + 1);

/* Check for a catch-all forward match */
SELECT COUNT(id) INTO does_exist FROM forwardings WHERE lower(source) = CONCAT('@', domain);
IF does_exist > 0 THEN
	SELECT id INTO match_id FROM forwardings WHERE lower(source) = CONCAT('@', domain);
END IF;

IF match_id > 0 THEN
	RETURN 0; -- Valid forward
END IF;

/* Finally we want to check the transports to see if we have a match there */
SELECT COUNT(id) INTO does_exist FROM transport WHERE lower(source) = _email;
IF does_exist > 0 THEN
	SELECT id INTO match_id FROM transport WHERE lower(source) = _email;
END IF;

IF match_id > 0 THEN
	RETURN 0; -- Valid transport
END IF;

/* Check to see if we have a domain transport match */
SELECT COUNT(id) INTO does_exist FROM transport WHERE lower(source) = domain;
IF does_exist > 0 THEN
	SELECT id INTO match_id FROM transport WHERE lower(source) = domain;
END IF;

IF match_id > 0 THEN
	RETURN 0; -- Valid transport
END IF;

/* Check to see if we have a subdomain transport match */
SELECT COUNT(id) INTO does_exist FROM transport WHERE lower(source) = CONCAT('.', domain);
IF does_exist > 0 THEN
	SELECT id INTO match_id FROM transport WHERE lower(source) = CONCAT('.', domain);
END IF;

IF match_id > 0 THEN
	RETURN 0; -- Valid transport
END IF;


RETURN 1; -- Invalid user 

END$$

DELIMITER ;
