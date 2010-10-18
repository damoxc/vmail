--
-- sql/mysql/resolve_forwards.fnc.sql
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

DROP PROCEDURE IF EXISTS `mail`.`resolve_forwards`$$
CREATE PROCEDURE `mail`.`resolve_forwards` ()
BEGIN

-- Create a new resolved_forwards table
CREATE TABLE `resolved_forwards_new` LIKE `resolved_forwards`;

-- Create a temporary table to keep forwards of forwards
CREATE TEMPORARY TABLE _resolved_forwards (
	source      varchar(80),
	destination varchar(250)
);

-- Insert all the forwards into the resolved table
INSERT INTO resolved_forwards_new (source, destination)
SELECT source, destination
FROM forwards f;

-- Loop over until there are no forwards pointing at forwards anymore
WHILE EXISTS (
	SELECT NULL FROM resolved_forwards_new f
	WHERE EXISTS (
		SELECT NULL FROM resolved_forwards_new ff
		WHERE f.destination = ff.source
	)
)
DO
	-- Add all forwards that point to a forward to the temporary
	INSERT INTO _resolved_forwards (source, destination)
	SELECT f.source, f.destination
	FROM resolved_forwards_new f
		INNER JOIN resolved_forwards_new ff ON ff.source = f.destination;

	-- Resolve all forwards that point to forwards one level down
	UPDATE resolved_forwards_new f
		INNER JOIN resolved_forwards_new ff ON ff.source = f.destination
	SET f.destination = ff.destination;
	
	-- Remove any looping forwards
	DELETE f
	FROM resolved_forwards_new f
		INNER JOIN resolved_forwards_new ff ON f.destination = ff.source
			AND f.source = ff.destination;
END WHILE;

INSERT INTO resolved_forwards_new (source, destination)
SELECT source, destination
FROM _resolved_forwards f
WHERE NOT EXISTS (
	SELECT NULL FROM resolved_forwards_new ff
	WHERE f.source = ff.source
		AND f.destination = ff.destination
);

-- Remove all forwards that aren't pointing to a user
DELETE f
FROM resolved_forwards_new f
WHERE NOT EXISTS (
	SELECT NULL FROM users u
	WHERE u.email = f.destination
);

-- Remove looping forwards
DELETE f
FROM resolved_forwards_new f
	INNER JOIN resolved_forwards_new ff ON ff.source = f.destination
		AND ff.destination = f.source
WHERE f.source < ff.source;

-- Remove any exact duplicates
DELETE f
FROM resolved_forwards_new f
INNER JOIN (
	SELECT source, destination, MIN(id) AS minId
	FROM resolved_forwards_new
	GROUP BY source, destination
	HAVING COUNT(*) > 1
) d ON d.source = f.source
	AND f.destination = d.destination
WHERE f.id != d.minId;

-- Remove the temporary table
DROP TABLE _resolved_forwards;

-- Rename the resolved_forwards table and place the new table as the active one
RENAME TABLE `resolved_forwards` TO `resolved_forwards_old`,
	`resolved_forwards_new` TO `resolved_forwards`;

-- Remove the old resolved_forwards table
DROP TABLE `resolved_forwards_old`;

END$$

DELIMITER ;
