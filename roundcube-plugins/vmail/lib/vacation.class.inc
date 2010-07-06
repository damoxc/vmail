<?php

require_once 'base.class.inc';

class Vacation extends Base
{
	public $keys = array(
		'email', 'subject', 'body', 'cache',
		'domain', 'created', 'active');
	
	public function __get($key)
	{
		if ($key == 'user') {
			return User::get_user($this->email);
		}
		return parent::__get($key);
	}

	public function save() {
		$params = $this->get_params();
		if (count($params) == 0) return;
		$this->client->core->save_vacation($this->id, $params);
	}

	/********************
	 * Static functions *
	 ********************/
	public static function get_vacation($email)
	{
		$vac = new Vacation();
		$data = $vac->client->core->get_vacation($email);
		$vac->load($data);
		return $vac;
	}

	public static function from_data($data)
	{
		$vac = new Vacation();
		$vac->load($data);
		return $vac;
	}
}
?>
