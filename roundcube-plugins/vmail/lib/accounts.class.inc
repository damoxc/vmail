<?php

require_once 'dbbase.class.inc';

function get_admin_count($accounts)
{
	$admin_count = 0;
	foreach ($accounts as $account) {
		if ($account->get('admin')) $admin_count++;
	}
	return $admin_count;
}

function format_accounts($accounts)
{
	foreach	($accounts as $account) {
		foreach (array_keys($account->data) as $col) {
			$row['vmail.' . $col] = $account->fget($col);
		}
		$_accounts[] = $row;
	}
	return $_accounts;
}

function format_accounts_with_usage($accounts)
{
	foreach	($accounts as $account) {
		foreach (array_keys($account->data) as $col) {
			$row['vmail.' . $col] = $account->fget($col);
		}
		$row['vmail.quota'] = show_bytes($account->get_usage()) . ' / ' . $row['vmail.quota'];
		$_accounts[] = $row;
	}
	return $_accounts;
}

class Account extends DBBase
{
	function __construct($id = null, $load = true)
	{
		parent::__construct();
		$this->id = $id;
		$this->data = array(
			'quota'      => $this->config->get('default_quota'),
			'enabled'    => 1,
			'admin'      => 0,
			'forwarding' => 'std',
			'autoreply_subject' => '',
			'autoreply_body'    => ''
		);

		if ($this->id && $load) $this->load();
	}

	/*
	 * Deletes the account from the system
	 */
	function delete()
	{
		$db = $this->db();
		$sql = "DELETE vacation FROM vacation INNER JOIN users ON vacation.email = users.email WHERE users.id = %i";
		$sql = str_replace("%i", $db->quote($this->id), $sql);
		$db->query($sql);

		$sql = "DELETE forwardings FROM forwardings INNER JOIN users ON forwardings.source = users.email WHERE users.id = %i";
		$sql = str_replace("%i", $db->quote($this->id), $sql);
		$db->query($sql);

		$sql = "SELECT email FROM users WHERE id = %i";
		$sql = str_replace("%i", $db->quote($this->id), $sql);
		$res = $db->query($sql);
		$email = $db->fetch_array($res);

		$sql = "DELETE FROM users WHERE id = %i";
		$sql = str_replace("%i", $db->quote($this->id), $sql);
		$db->query($sql);

		delmaildir($email[0]);
	}

	/*
	 * Loads the values from the database
	 */
	function load()
	{
		$db = $this->db();
		$sql = "SELECT u.*, f.destination, v.subject AS 'autoreply_subject', v.body AS 'autoreply_body' FROM users u LEFT OUTER JOIN forwardings f ON u.email = f.source LEFT OUTER JOIN vacation v ON u.email = v.email WHERE u.id = %u ";
		$sql = str_replace('%u', $db->quote($this->id), $sql);
		$res = $db->query($sql);
		$row = $db->fetch_assoc($res);
		$this->_process_row($row);
		$this->forward = null;
	}

	function _process_row($row)
	{
		$this->data = $row;
		$this->is_admin = $row['admin'];

		if (!$row['destination']) {
			$this->data['forwarding'] = 'std';
			$this->data['forwardto'] = '';
			$this->data['savecopy'] = false;
			return;
		}

		$destinations = array_map("trim", explode(',', $row['destination']));

		// We want to check to see if autoreply is enabled on the account
		$autoreply_email = str_replace('@', '#', $this->data['email']);
		$autoreply_email .= '@' . $this->config->get('autoreply_domain');

		$this->data['autoreply'] = in_array($autoreply_email, $destinations);
		if ($this->data['autoreply']) {

			// Autoreply is enabled
			if (count($destinations) == 2 && in_array($this->data['email'], $destinations)) {
				// The only other address is ours
				$this->data['forwarding'] = 'std';
				$this->data['forwardto'] = '';
				$this->data['savecopy'] = false;
				return;
			}

			// There are more addresses so we want to remove our address
			$i = array_search($autoreply_email, $destinations);
			unset($destinations[$i]);
			$destinations = array_merge($destinations);
		}

		// Check to see if we are saving a copy of this email.
		$this->data['savecopy'] = in_array($this->data['email'], $destinations);
		if ($this->data['savecopy']) {
			$i = array_search($this->data['email'], $destinations);
			unset($destinations[$i]);
			$destinations = array_merge($destinations);
		}

		if (count($destinations) == 1) {
			$this->data['forwardto'] = $destinations[0];
		} else {
			$this->data['forwardto'] = implode(', ', $destinations);
		}

		$this->data['forwarding'] = 'fwd';

		unset($row['destination']);
	}

	/*
	 * Create the account in the database
	 */
	function create()
	{
		$email = $this->data['email'] . "@" . $this->vmail->domain_name;

		$db = $this->db();
		$sql = "INSERT INTO users (domain_id, email, name, password, cleartext, quota, enabled, admin) VALUES (%d, %m, %n, ENCRYPT(%p), %p, %q, %e, %a);";
		$sql = str_replace('%d', $db->quote($this->data['domain_id']), $sql);
		$sql = str_replace('%m', $db->quote($email), $sql);
		$sql = str_replace('%n', $db->quote($this->data['name']), $sql);
		$sql = str_replace('%p', $db->quote($this->data['password']), $sql);
		$sql = str_replace('%q', $db->quote($this->data['quota']), $sql);
		$sql = str_replace('%e', $db->quote($this->data['enabled']), $sql);
		$admin = ($this->data['admin']) ? 1 : 0;
		$sql = str_replace('%a', $db->quote($this->data['admin']), $sql);
		$db->query($sql);
		$this->id = $db->insert_id();

		// Create new OOO message
		$sql = "INSERT INTO `vacation` VALUES (%e, %s, %b, '', %d, NOW(), 1);";
		$sql = str_replace('%e', $db->quote($email), $sql);
		$sql = str_replace('%s', $db->quote($this->data['autoreply_subject']), $sql);
		$sql = str_replace('%b', $db->quote($this->data['autoreply_body']), $sql);
		$sql = str_replace('%d', $db->quote($this->vmail->domain), $sql);
		$db->query($sql);

		// TODO: create forwarding if required.
		$destination = $this->get_destination();
		if ($destination) {
			// if we have a destination we need to update the forward.
			$sql = "INSERT INTO `forwardings` (`domain_id`, `source`, `destination`) VALUES (%i, %s, %d);";
			$sql = str_replace('%i', $db->quote($this->vmail->domain_id), $sql);
			$sql = str_replace('%d', $db->quote($destination), $sql);
			$sql = str_replace('%s', $db->quote($email), $sql);
			$db->query($sql);
		}
	}

	/*
	 * Save any modified values to the database
	 */
	function save()
	{
		if (!count($this->modified)) return; // return if nothing has been changed.
		if (!$this->id) return $this->create(); // run create() if we don't have an id

		$db = $this->db();
		$sql = "";
		$ignore = array('autoreply', 'autoreply_subject', 'autoreply_body', 'forwarding', 'forwardto', 'savecopy');

		foreach ($this->modified as $key => $val) {
			if ($key == 'password') {
				$sql .= "`password` = ENCRYPT(" . $db->quote($this->data[$key]) . "), ";
				$sql .= "`cleartext` = " . $db->quote($this->data[$key]) . ", ";
			} else if (in_array($key, $ignore)) {
				continue;
			} else if ($key == 'email') {
				$email = $this->data['email'] . "@" . $this->vmail->domain_name;
				$sql .= $db->quote_identifier($key) . " = " . $db->quote($email) . ", ";
			} else {
				$sql .= $db->quote_identifier($key) . " = " . $db->quote($this->data[$key]) . ", ";
			}
		}

		// Only execute the $sql if values have been modified.
		if ($sql) {
			$sql = "UPDATE `users` SET" . substr($sql, 0, -2) . " WHERE `id` = " . $db->quote($this->id) . ";";
			$db->query($sql);
		}

		// Only update the vacation table if our OOO message has been changed.
		if (in_array("autoreply_subject", $this->modified) || in_array("autoreply_body", $this->modified)) {
			
			$sql = "REPLACE INTO `vacation` SET ";
			$sql	.= "`email` = %e, ";
			$sql	.= "`subject` = %s, ";
			$sql	.= "`body` = %b, ";
			$sql	.= "`created` = NOW(), ";
			$sql	.= "`active` = 1;";

			$sql = str_replace('%e', $db->quote($this->data['email']), $sql);
			$sql = str_replace('%s', $db->quote($this->data['autoreply_subject']), $sql);
			$sql = str_replace('%b', $db->quote($this->data['autoreply_body']), $sql);
			$db->query($sql);
		}

		if (in_array("autoreply", $this->modified)) {
			$sql = "DELETE FROM `vacation_notification` WHERE on_vacation = %e";
			$sql = str_replace('%e', $db->quote($this->data['email']), $sql);
			$db->query($sql);
		}

		$destination = $this->get_destination();
		if ($destination) {
			// if we have a destination we need to update the forward.
			$sql = "REPLACE INTO `forwardings` SET `domain_id` = %i, `source` = %s, `destination` = %d;";
			$sql = str_replace('%i', $db->quote($this->vmail->domain_id), $sql);
			$sql = str_replace('%d', $db->quote($destination), $sql);
			$sql = str_replace('%s', $db->quote($this->data['email']), $sql);
		} else {
			// we need to delete the forward if we don't.
			$sql = "DELETE FROM `forwardings` WHERE `source` = %s";
			$sql = str_replace('%s', $db->quote($this->data['email']), $sql);
		}
		$db->query($sql);
	}

	private function get_destination()
	{
		if ($this->data['autoreply']) {
			$autoreply_email = str_replace('@', '#', $this->data['email']);
			$autoreply_email .= '@' . $this->config->get('autoreply_domain');

			if ($this->data['forwarding'] == 'fwd') {
				if ($this->data['savecopy']) {
					return $this->data['email'] . ',' . $autoreply_email . ',' . $this->data['forwardto'];
				} else {
					return $autoreply_email . ',' . $this->data['forwardto'];
				}
			} else {
				return $this->data['email'] . ',' . $autoreply_email;
			}
		} else {
			// handle forwarding with no autoreply.
			if ($this->data['forwarding'] == 'fwd') {
				if ($this->data['savecopy']) {
					return $this->data['email'] . ',' . $this->data['forwardto'];
				} else {
					return $this->data['forwardto'];
				}
			}
		}
	}

	function get_domain()
	{
		return new Domain($this->data['domain_id']);
	}

	function get_usage()
	{
		return get_maildir_size($this->data['email']);
	}

	function fget($key)
	{
		if ($key == 'quota') {
			return show_bytes($this->data[$key]);
		} else if ($key == 'enabled') {
			return ($this->data[$key]) ? $this->vmail->gettext('yes') : $this->vmail->gettext('no');
		} else {
			return $this->data[$key];
		}
	}

	function set($key, $value)
	{
		// once an id has been set we don't want to change the email
		if ($key == 'email' && $this->id > 0) return;
		//if ($key == 'email') $value .= "@" . $this->vmail->domain_name;
		parent::set($key, $value);
	}

	/********************
	 * Static functions *
	 ********************/
	public static function get_by_username($username)
	{
		$db = DBBase::get_db();
		$sql = "SELECT u.*, f.destination, v.subject AS 'autoreply_subject', v.body AS 'autoreply_body' FROM users u LEFT OUTER JOIN forwardings f ON u.email = f.source LEFT OUTER JOIN vacation v ON u.email = v.email  WHERE u.email = %u";
		$sql = str_replace('%u', $db->quote($username), $sql);
		$res = $db->query($sql);
		$row = $db->fetch_assoc($res);

		$account = new Account($row['id'], false);
		$account->_process_row($row);
		return $account;
	}

	private static function _get_all($domain)
	{
		$db = DBBase::get_db();
		if (is_int($domain)) {
			$sql = "SELECT * FROM users WHERE domain_id = %d";
		} else {
			 $sql = "SELECT u.* FROM users u INNER JOIN domains d ON u.domain_id = d.id WHERE d.domain = %d";
		}

		$sql = str_replace('%d', $db->quote($domain), $sql);
		$res = $db->query($sql);

		while ($row = $db->fetch_assoc($res)) {
			$account = new Account(null, false);
			$account->_process_row($row);
			$account->id = $account->data['id'];
			$accounts[] = $account;
		}
		return $accounts;
	}

	public static function get_all_by_domain($domain)
	{
		return Account::_get_all($domain);
	}

	public static function get_all_by_domain_id($domain_id)
	{
		return Account::_get_all($domain_id);
	}

	public static function can_edit($domain_id, $aid)
	{
		// This means the account hasn't been created yet
		if ($aid == -1 || $aid == 0) return true;

		$db = DBBase::get_db();
		$sql = "SELECT domain_id FROM users WHERE id = %i";
		$sql = str_replace('%i', $db->quote($aid), $sql);
		$res = $db->query($sql);
		if ($row = $db->fetch_array($res))
			return $row[0] == $domain_id;
		return false;
	}
}

?>
