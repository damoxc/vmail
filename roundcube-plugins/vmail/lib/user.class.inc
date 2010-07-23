<?php

require_once 'base.class.inc';

class User extends Base
{
	public $keys = array(
		'domain_id', 'email', 'secondary_email', 'name', 'password',
		'cleartext', 'quota', 'usage', 'enabled', 'admin');
	
	public function __get($key)
	{
		if (!array_key_exists($key, $this->cache)) {
			switch ($key) {
				case 'domain':
					$this->cache['domain'] = Domain::get_domain($this->domain_id);
					break;

				case 'forward':
					$this->cache['forward'] = Forward::get_forward($this->email);
					break;

				case 'forwarding':
					$forward = $this->forward;
					if ($forward->id == 0) {
						$this->cache['forwarding'] = 'std';
						$this->cache['forwardto'] = '';
						$this->cache['savecopy'] = false;
						break;
					}
					
					$destinations = array_map("trim", explode(',', $forward->destination));

					// Check autoreply
					$autoreply_email = str_replace('@', '#', $this->email);
					$autoreply_email .= '@' . $this->config['autohost'];

					if (in_array($autoreply_email, $destinations)) {
						if (count($destinations) == 2 && in_array($this->data['email'], $destinations)) {
							$this->cache['forwarding'] = 'std';
							$this->cache['forwardto'] = '';
							$this->cache['savecopy'] = false;
							break;
						}

						// There are more addresses so we want to remove the vacation address
						$i = array_search($autoreply_email, $destinations);
						unset($destinations[$i]);
						$destinations = array_merge($destinations);
					}

					$this->cache['savecopy'] = in_array($this->data['email'], $destinations);
					if ($this->cache['savecopy']) {
						$i = array_search($this->data['email'], $destinations);
						unset($destinations[$i]);
						$destinations = array_merge($destinations);
					}

					if (count($destinations) == 1) {
						$this->cache['forwardto'] = $destinations[0];
					} else {
						$this->cache['forwardto'] = implode(', ', $destinations);
					}
					$this->data['forwarding'] = 'fwd';
					break;

				case 'vacation':
					$this->cache['vacation'] = Vacation::get_vacation($this->email);
					break;
			}
		}
		return parent::__get($key);
	}

	public function fget($key)
	{
		if ($key == 'quota' || $key == 'usage') {
			return show_bytes($this->data[$key]);
		} else if ($key == 'enabled') {
			return ($this->data[$key]) ? $this->gettext('yes') : $this->gettext('no');
		} else {
			return $this->data[$key];
		}
	}

	public function delete()
	{
		$this->client->core->delete_user($this->id);
	}

	public function save()
	{
		$params = $this->get_params();
		if (count($params) == 0) return;
		$result = $this->client->core->save_user($this->id, $params);
		if ($result > 0) $this->id = $result;
	}
	
	/********************
	 * Static functions *
	 ********************/
	public static function get_user($username)
	{
		$user = new User();
		$data = $user->client->core->get_user($username);
		$user->load($data);
		return $user;
	}

	public static function from_data($data)
	{
		$user = new User();
		$user->load($data);
		return $user;
	}
}
?>
