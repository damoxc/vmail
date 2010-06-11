<?php

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
	$cmd = 'vgetconfig "%k"';
	$cmd = str_replace('%k', $key, $cmd);
	$output = explode(':', exec($cmd), 2);
	return trim($output[1]);
}

?>
