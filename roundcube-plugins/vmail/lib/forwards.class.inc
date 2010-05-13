<?php

require_once 'dbbase.class.inc';

class Forward extends DBBase
{
	public $table = 'forwardings';

	function __construct($id = null, $load = true)
	{
		parent::__construct();
		$this->id = $id;
		$this->data = array(
			'source'   => '',
			'catchall' => false
		);

		if ($this->id && $load) $this->load();
	}

	function load()
	{
		$db = $this->db();
		$sql = "SELECT f.* FROM forwardings f WHERE f.id = %f";
		$sql = str_replace('%f', $db->quote($this->id), $sql);
		$res = $db->query($sql);
		$row = $db->fetch_assoc($res);
		$row['catchall'] = ($row['source'] == '@' . DBBase::$vmail->domain_name);
		$this->data = $row;
	}

	/*
	 * Create the forward in the database
	 */
	function create()
	{
		$db = $this->db();
		$sql = "INSERT INTO forwardings (domain_id, source, destination) ";
		$sql .= "VALUES (%d, %s, %f)";
		$sql = str_replace('%d', $db->quote($this->data['domain_id']), $sql);
		$sql = str_replace('%s', $db->quote($this->data['source']), $sql);
		$sql = str_replace('%f', $db->quote($this->data['destination']), $sql);
		$db->query($sql);
		if ($db->db_error) {
			$error = $db->db_handle->errorInfo();
			if ($error[1] == 1062) {
				return 1;
			} else {
				return 2;
			}
		}
		$this->id = $db->insert_id();
		return 0;
	}

	/*
	 * Store the forward in the database
	 */
	function save()
	{
		if (!count($this->modified)) return 0; // return if nothing has been changed.
		if (!$this->id) return $this->create(); // run create() if we don't have an id

		$db = $this->db();
		$sql = "UPDATE `forwardings` SET ";
		foreach ($this->modified as $key => $val) {
			$sql .= $db->quote_identifier($key) . " = " . $db->quote($this->data[$key]) . ", ";
		}
		$sql = substr($sql, 0, -2);
		$sql .= " WHERE `id` = " . $db->quote($this->id) . ";";
		$db->query($sql);
		return 0;
	}

	public static function get_by_source($source)
	{
		$db = DBBase::get_db();
		$sql = "SELECT * FROM forwardings WHERE source = %s";
		$sql = str_replace('%s', $db->quote($source), $sql);

		$res = $db->query($sql);
		$row = $db->fetch_assoc($res);
		$row['catchall'] = ($row['source'] == '@' . DBBase::$vmail->domain);
		$forward = new Forward(null, false);
		$forward->data = $row;
		$forward->id = $row['id'];
		return $forward;
	}
}

?>
