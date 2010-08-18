<?php

/**
 * Vmail plugin that warns when close to reaching quota limits.
 */

require_once dirname(dirname(__FILE__)) . '/vmail/lib/funcs.inc';
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

		$domain = get_domain_part($email);
		$user = get_user_part($email);

		$this->client = new VClient();
		$domain_used = $this->client->core->get_usage($domain);
		$domain_quota = $this->client->core->get_quota($domain);

		$user_user = $this->client->core->get_usage($domain, $user);
		$user_quota = $this->client->core->get_quota($domain, $user);

		$domain_usage = ceil(($domain_used / $domain_quota) * 100);
		$user_usage = ceil(($user_used / $user_quota) * 100);

		if ($domain_usage >= 85) {
			$this->rcmail->output->show_message('vmail_quota.domainusage', 'error',
				array('usage' => $domain_usage));
		}

		if ($user_usage >= 85) {
			$this->rcmail->output->show_message('vmail_quota.userusage', 'error',
				array('usage' => $user_usage));
		}

		if ($domain_usage >= 85 && $user_usage >= 85) {
			$this->rcmail->output->show_message('vmail_quota.domainuserusage', 'error',
				array('user_usage' => $user_usage, 'domain_usage' => $domain_usage));
		}
	}
}
?>
