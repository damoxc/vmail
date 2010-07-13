--
-- sql/mysql/is_local.fnc.sql
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

DROP FUNCTION `is_local`
CREATE `is_local`(
	_email VARCHAR(255)
) RETURNS int(11)
BEGIN

DECLARE domain VARCHAR(50);
DECLARE does_exist INT;
DECLARE user_enabled INT;
DECLARE match_id INT;

SET does_exist = 0;
SET domain = SUBSTRING(_email, LOCATE('@', _email) + 1);

SELECT COUNT(id) INTO does_exist FROM users WHERE email = _email;
IF does_exist > 0 THEN
	SELECT id, enabled INTO match_id, user_enabled FROM users WHERE email = _email;
END IF;

IF match_id > 0 AND user_enabled > 0 THEN
	RETURN 1;
ELSEIF match_id > 0 AND user_enabled = 0 THEN
	RETURN 0; 
END IF;

RETURN 0;

END$$

DELIMITER ;
