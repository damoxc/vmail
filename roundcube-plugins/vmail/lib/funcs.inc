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
 * @param Forward $a The first forward
 * @param Forward $b The forward to compare with
 */
function fwdcmp($a, $b) {
	return strcmp($a->source, $b->source);
}

/**
 * Converts an associative array into a string
 * that can be used for a style attribute.
 * @param  array  $attrib The attributes to use
 * @return string         The style attribute
 */
function style_string($attrib) {
	foreach ($attrib as $k => $v) {
		$args[] = "$k: $v";
	}
	return implode('; ', $args);
}

/**
 * Generate out the HTML for displaying a quota bar.
 * @param  int    $usage The total usage in bytes
 * @param  int    $quota The total quota in bytes
 * @return string        The HTML for the quota bar.
 */
function quota_bar($usage, $quota) {

	$percent = intval(($usage / $quota) * 100);
	$title = rcube_label('quota') . ': ';
	$title .= sprintf('%s / %s (%.0f%%)',
		show_bytes($usage), show_bytes($quota), $percent);
	

	// Make the quota background image
	$out = '<div id="accounts-quota">';
	$out .= html::img(array(
		'class' => 'quotaimg',
		'src'   => 'skins/default/images/quota.gif',
		'alt'   => '',
		'title' => $title));
	$out .= '</div>';

	// Begin the quota bar
	$out .= '<div class="quota">';
	$out .= '<span class="quotadisplay">';

	$style = 'position: absolute; height: 14px; ';
	if ($percent >= 80) {
		$class = 'quota_high';
		$txt_class = 'quota_text_high';
	} else if ($percent >= 55) {
		$class = 'quota_mid';
		$txt_class = 'quota_text_mid';
	} else {
		$class = 'quota_low';
		$txt_class = 'quota_text_normal';
	}

	// Create the bar background layer
	$out .= html::div(array(
		'style' => style_string(array(
			'position' => 'absolute',
			'height'   => '14px',
			'top'      => '1px',
			'left'     => '1px',
			'z-index'  => '99',
			'width'    => "${percent}px")),
		'class' => $class
		));
	
	// Create the whole background layer
	$out .= html::div(array(
		'style' => style_string(array(
			'position' => 'absolute',
			'height'   => '14px',
			'top'      => '1px',
			'left'     => '1px',
			'z-index'  => '98',
			'width'    => '100px')),
		'class' => 'quota_bg'
		));
	
	// Create the text layer
	$out .= html::div(array(
		'style' => style_string(array(
			'position' => 'absolute',
			'height'   => '14px',
			'top'      => '0px',
			'left'     => '0px',
			'z-index'  => '100',
			'width'    => '100px')),
		'class' => 'quota_text ' . $txt_class,
		'title' => $title), "${percent}%");

	$out .= '</span>';
	$out .= '</div>';

	return $out;
}

?>
