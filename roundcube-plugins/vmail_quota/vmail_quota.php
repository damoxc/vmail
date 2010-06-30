<?php

/**
 * Vmail plugin that displays the domain quota in the mailview.
 */

require_once dirname(dirname(__FILE__)) . '/vmail/lib/vclient.class.inc';

class vmail_quota extends rcube_plugin
{
	public $task = 'mail';

	function init()
	{
		$this->rcmail = &rcmail::get_instance();
		$email = $this->rcmail->user->data['username'];
		if (strlen($email) == 0) return;

		$this->add_texts('localization/', array('vmail_quota'));

		$domain = substr($email, strrpos($email, '@') + 1);

		$this->client = new VClient();
		$used = $this->client->core->get_usage($domain);
		$quota = $this->client->core->get_quota($domain);

		$usage = $used / $quota * 100.0;
		if ($usage > 100)
			$usage = 100;

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
