<?php

require_once 'base.class.inc';

class Domain extends Base
{
	public $keys = array('login_id', 'domain', 'package', 'package_id', 'quota', 'account_limit', 'enabled');

	function __construct($id = null, $load = true)
	{
		parent::__construct();
		$this->id = $id;
		$this->data = array(
			'package'  => 'Webmail 50',
			'quota'    => 52428800,
			'accounts' => 5
		);

		if ($this->id && $load) $this->load();
	}

	function __get($key)
	{
		if (!array_key_exists($key, $this->cache)) {
			switch ($key) {
				case 'user_count':
					$this->cache['user_count'] = $this->client->core->get_user_count($this->id);
					break;

				case 'usage':
					$this->cache['usage'] = $this->client->core->get_usage($this->id);
					break;

				case 'forwards':
					$fwd_data = $this->client->core->get_forwards($this->id);
					foreach ($fwd_data as $k => $v) {
						
						$forwards[] = Forward::from_data(array(
							'source'       => $k, 
							'destinations' => $v,
							'domain_id'    => $this->id
						));
					}
					$this->cache['forwards'] = $forwards;
					break;

				case 'users':
					$users_data = $this->client->core->get_users($this->id);
					foreach ($users_data as $data) {
						$users[] = User::from_data($data);
					}
					return $users;
			}
		}

		return parent::__get($key);
	}

	// TODO: check for permission
	function can_create_account()
	{
		if ($this->account_limit != -1 &&
				$this->user_count >= $this->account_limit)
			return false;

		return true;
	}

	function can_edit_account($aid)
	{
		if (!$aid) return true;

		$account = new Account($aid);
		return ($account->get('domain_id') == $this->id);
	}

	/********************
	 * Static functions *
	 ********************/
	public static function get_domain($domain_name)
	{
		$domain = new Domain();
		$data = $domain->client->core->get_domain($domain_name);
		$domain->load($data);
		return $domain;
	}

	public static function from_data($data)
	{
		$domain = new Domain();
		$domain->load($data);
		return $domain;
	}
}
?>
