<?php

/**
 * Vmail plugin that displays the domain quota in the mailview.
 */

class vmail_quota extends rcube_plugin
{
	public $task = 'mail';

	function init()
	{
		$this->rcmail = &rcmail::get_instance();
		$email = $this->rcmail->user->data['username'];
		if (strlen($email) == 0) return;

		$this->add_texts('localization/', array('vmail_quota'));
		$cmd = 'sudo -u vmail /usr/bin/getmaildirsize -q "%d"';
		$email = substr($email, strrpos($email, '@') + 1);
		$cmd = str_replace('%d', $email, $cmd);
		$output = explode('/', exec($cmd));
		$used = floatval($output[0]);
		$quota = floatval($output[1]);
		$usage = $used / $quota * 100.0;

		$this->rcmail->output->set_env('dom_quota', array(
			'usage' => intval($usage),
			'used'  => show_bytes($used),
			'total' => show_bytes($quota)
		));
		$this->include_script('jquery.create.js');
		$this->include_script('vmail_quota.js');
	}
}
?>
