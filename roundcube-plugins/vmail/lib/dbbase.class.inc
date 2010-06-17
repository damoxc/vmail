<?php

class DBBase
{
	public static $vmail;
	public $table = null;

	function __construct()
	{
		$this->config = DBBase::$vmail->config;
		$this->data = array();
		$this->modified = array();
		$this->vmail = DBBase::$vmail;
	}

	public static function get_db()
	{
		$db = new rcube_mdb2(DBBase::$vmail->config['rwdburi'], '', FALSE);
		$db->set_debug((bool)DBBase::$vmail->rcmail->config->get('sql_debug'));
		$db->db_connect('w');
		return $db;
	}

	function db()
	{
		return DBBase::get_db();
	}

	function delete()
	{
		if (!$this->table) return;
		$db = $this->db();
		$sql = "DELETE FROM " . $db->quote_identifier($this->table) . " WHERE `id` = %i";
		$sql = str_replace("%i", $db->quote($this->id), $sql);
		$db->query($sql);
	}

	function get($key)
	{   
		return $this->data[$key];
	}

	function fget($key)
	{
		return $this->data[$key];
	}

	function set($key, $value)
	{
		if ($this->data[$key] == $value) return;
		$this->data[$key] = $value;
		$this->modified[$key] = true;
	}
}

?>
