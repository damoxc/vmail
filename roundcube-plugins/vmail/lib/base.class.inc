<?php

class Base
{
	public static $vmail;
	public $table = null;
	public $client = null;
	public $config = null;
	public $data = null;
	public $_modified = null;
	public $cache = null;
	public $keys = null;
	public $id = null;

	function __construct($id = null)
	{
		$this->client = Base::$vmail->client;
		$this->config = Base::$vmail->config;
		$this->data = array();
		$this->_modified = array();
		$this->cache = array();
		$this->id = $id;
	}

	function gettext($key)
	{
		return Base::$vmail->gettext($key);
	}

	function load($data)
	{
		$this->id = $data->id;
		foreach ($this->keys as $key) {
			$this->data[$key] = (is_array($data)) ? $data[$key] : $data->$key;
		}
	}

	protected function get_params()
	{
		foreach ($this->_modified as $key => $value) {
			$params[$key] = $this->$key;
		}
		return $params;
	}

	function __get($key)
	{
		if (array_key_exists($key, $this->cache)) {
			return $this->cache[$key];
		} else {
			return $this->data[$key];
		}
	}

	function format($key)
	{
		return $this->data[$key];
	}
	
	function modified($key)
	{
		return array_key_exists($key, $this->_modified);
	}

	function __set($key, $value)
	{
		if ($this->data[$key] == $value) return; // No point setting it if they are the same
		if (!in_array($key, $this->keys)) return; // Don't set keys that aren't ours
		$this->data[$key] = $value;
		$this->_modified[$key] = true;
	}
}

?>
