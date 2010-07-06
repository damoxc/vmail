<?php

require_once 'base.class.inc';

class Forward extends Base
{
	public $keys = array('domain_id', 'source', 'destination');

	public function __get($key)
	{
		if ($key == 'catchall') {
			return ($this->source[0] == '@');
		}
		return parent::__get($key);
	}

	public function delete()
	{
		$this->client->core->delete_forward($this->id);
	}

	public function save()
	{
		$params = $this->get_params();
		if (count($params) == 0) return;
		$result = $this->client->core->save_forward($this->id, $params);
		if ($result > 0) $this->id = $result;
	}

	public static function get_forward($source)
	{
		$fwd = new Forward();
		$data = $fwd->client->core->get_forward($source);
		$fwd->load($data);
		return $fwd;
	}

	public static function from_data($data)
	{
		$fwd = new Forward();
		$fwd->load($data);
		return $fwd;
	}
}

?>
