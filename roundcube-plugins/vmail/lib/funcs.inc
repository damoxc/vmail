<?php

$vmail_cfg = array();

function array_insert($array, $index, $value) {
	array_splice($array, $index, count($array), array_merge(array($value), array_slice($array, $index)));
}

function get_domain_part($email) {
	$pos = strrpos($email, '@');
	return substr($email, $pos + 1);
}

function get_user_part($email) {
	$pos = strrpos($email, '@');
	return substr($email, 0, $pos);
}

function get_maildir_size($username) {
	$cmd = 'sudo -u vmail /usr/bin/getmaildirsize "%e"';
	$cmd = str_replace('%e', $username, $cmd);
	return intval(exec($cmd));
}

function createmaildir($email) {
	$cmd = '/usr/bin/createmaildir "%e"';
	$cmd = str_replace('%e', $email, $cmd);
	exec($cmd);
}

function delmaildir($email) {
	$cmd = 'sudo -u vmail /usr/bin/delmaildir "%e"';
	$cmd = str_replace('%e', $email, $cmd);
	exec($cmd);
}

function getconfig($key) {
	global $vmail_cfg;
	if (!count($vmail_cfg)) {
		$fh = fopen('/etc/vmail/vmail.cfg', 'r');
		$cfg_contents = fread($fh, 2048);
		fclose($fh);
		$vmail_cfg = json_decode($cfg_contents, true);
	}
	return $vmail_cfg[$key];
}

/**
 * Comparison function for a list of forwards
 * @param $a Forward
 * @param $b Forward
 */
function fwdcmp($a, $b) {
	return strcmp($a->source, $b->source);
}

?>
