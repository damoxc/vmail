<?php

require_once 'dbbase.class.inc';

class Domain extends DBBase
{
	public $table = 'domains';

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

	function load()
	{
		$db = $this->db();
		$sql = "SELECT d.*, (SELECT count(id) FROM users WHERE domain_id = d.id) AS 'accounts' FROM domains d WHERE id = %i";
		$sql = str_replace('%i', $db->quote($this->id), $sql);
		$res = $db->query($sql);
		$row = $db->fetch_assoc($res);
		$this->data = $row;
	}

	/*
	 * Create the domain in the database
	 */
	function create()
	{
	}

	/*
	 * Store the forward in the database
	 */
	function save()
	{
		// return if nothing has been changed.
		if (!count($this->modified)) return 0;

		// run create() if we don't have an id
		if (!$this->id) return $this->create();
	}

	// TODO: check for permission
	function can_create_account()
	{
		if ($this->data['account_limit'] != -1 && 
				$this->data['accounts'] >= $this->data['account_limit'])
			return false;

		return true;
	}

	function can_edit_account($aid)
	{
		if (!$aid) return true;

		$account = new Account($aid);
		return ($account->get('domain_id') == $this->id);
	}

	function get_accounts()
	{
		$db = $this->db();
		$sql = "SELECT u.*, f.destination, v.subject AS 'autoreply_subject', v.body AS 'autoreply_body' FROM users u LEFT OUTER JOIN forwardings f ON u.email = f.source LEFT OUTER JOIN vacation v ON u.email = v.email WHERE u.domain_id = %d";
		$sql = str_replace('%d', $db->quote($this->id), $sql);
		$res = $db->query($sql);

		while ($row = $db->fetch_assoc($res)) {
			$account = new Account($row['id'], false);
			$account->_process_row($row);
			$accounts[] = $account;
		}
		return $accounts;
	}

	function get_usage() {
		return get_maildir_size($this->data['domain']);
	}

	public static function get_by_name($domain_name)
	{
		$db = DBBase::get_db();
		$sql = "SELECT * FROM domains WHERE domain = %d";
		$sql = str_replace('%d', $db->quote($domain_name), $sql);

		$res = $db->query($sql);
		$row = $db->fetch_assoc($res);
		$domain = new Domain($row['id'], false);
		$forward->data = $row;
		return $forward;
	}
}

?>
