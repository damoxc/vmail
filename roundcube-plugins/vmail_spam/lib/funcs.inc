<?php

function learnham($username, $folder, $uid) {
	$cmd = 'sudo -u vmail learnham "%e" "%f" "%u"';
	$cmd = str_replace('%e', $username, $cmd);
	$cmd = str_replace('%f', $folder, $cmd);
	$cmd = str_replace('%u', $uid, $cmd);
	return intval(exec($cmd));
}

function learnspam($username, $folder, $uid) {
	$cmd = 'sudo -u vmail learnspam "%e" "%f" "%u"';
	$cmd = str_replace('%e', $username, $cmd);
	$cmd = str_replace('%f', $folder, $cmd);
	$cmd = str_replace('%u', $uid, $cmd);
	console("executing: $cmd");
	return intval(exec($cmd));
}

?>
