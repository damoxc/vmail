<?php

/**
 * VMail plugin that allows for account management, forwarding setup,
 * autoreplies to be setup.
 *
 * @package plugins
 * @uses    rcube_plugin
 * @author  Damien Churchil <damoxc@gmail.com>
 * @version 0.1
 * @license GPL
 * @link    https://www.uk-plc.net/os/rcube-vmail
 *
 */

require_once 'lib/funcs.inc';
require_once 'lib/vclient.class.inc';
require_once 'lib/base.class.inc';
require_once 'lib/domain.class.inc';
require_once 'lib/forward.class.inc';
require_once 'lib/user.class.inc';
require_once 'lib/vacation.class.inc';

class vmail extends rcube_plugin
{
	public $task = 'settings';

	function init()
	{
		$this->rcmail = &rcmail::get_instance();
		$this->client = new VClient();

		$this->add_texts('localization/', array('vmail'));
		$this->config = array(
			'dburi'    => getconfig('rwdburi'),
			'autohost' => getconfig('autohost')
		);
		// Configure the base class
		Base::$vmail = $this;

		// Get the current user
		$username = $this->rcmail->user->data['username'];

		// This means we aren't logged in
		if (!$username) return;

		$this->user = User::get_user($username);

		// This means that there is some issue with vmaild
		if (!$this->user->id) return;

		// Set up modifying the out of office message via the preferences
		// tab in settings and changing passwords.
		$this->add_hook('list_prefs_sections', array($this, 'listprefs_handler'));
		$this->add_hook('user_preferences', array($this, 'prefs_handler'));
		$this->add_hook('save_preferences', array($this, 'prefs_save_handler'));

		$this->include_script('vmail_passwd.js');

		// Get the domain information from the database.
		$this->domain = $this->user->domain;
	
		//$this->domain = $this->client->core->get_domain($this->user->domain_id);
		$this->domain_id = $this->domain->id;
		$this->domain_name = $this->domain->domain;
		$this->set_env('uid', $this->user->id);

		// If the user isn't an admin we can't continue.
		if (!$this->user->admin) return;

		// Set the id of the current account being editing to 0.
		$this->aid = 0;

		$pos = strrpos($user->data['username'], '@');
		$this->username = substr($user->data['username'], 0, $pos);
		$this->rcmail->output->set_env('user', $this->user->email);

		// Finish setting up the plugin
		$this->include_script('vmail.js');
		$this->include_stylesheet('vmail.css');

		// Register the accounts actions
		$this->register_action('plugin.accounts',
			array($this, 'accounts_handler'));
		$this->register_action('plugin.add-account',
			array($this, 'add_account_handler'));
		$this->register_action('plugin.delete-account',
			array($this, 'delete_account_handler'));
		$this->register_action('plugin.edit-account',
			array($this, 'edit_account_handler'));
		$this->register_action('plugin.save-account',
			array($this, 'save_account_handler'));

		// Register the accounts handlers
		$this->register_handler('plugin.accountslist',
			array($this, 'accountslist_html'));
		$this->register_handler('plugin.accounts-count',
			array($this, 'accounts_count_html'));
		$this->register_handler('plugin.accountsquota',
			array($this, 'accountsquota_html'));
		$this->register_handler('plugin.accounteditform',
			array($this, 'accounteditform_html'));

		// Register the forwards actions
		$this->register_action('plugin.forwards',
			array($this, 'forwards_handler'));
		$this->register_action('plugin.add-forward',
			array($this, 'add_forward_handler'));
		$this->register_action('plugin.delete-forward',
			array($this, 'delete_forward_handler'));
		$this->register_action('plugin.edit-forward',
			array($this, 'edit_forward_handler'));
		$this->register_action('plugin.save-forward',
			array($this, 'save_forward_handler'));

		// Register the forwards handlers
		$this->register_handler('plugin.forwardslist',
			array($this, 'forwardslist_html'));
		$this->register_handler('plugin.forwardeditform',
			array($this, 'forwardeditform_html'));
	}

	function listprefs_handler($args)
	{
		// Add Password to the preferences sections list
		$args['list']['password'] = array(
			'id'      => 'password',
			'section' => Q($this->gettext('password'))
		);
		// Add Out of Office to the preferences sections list
		$args['list']['outofoffice'] = array(
			'id' => 'outofoffice',
			'section' => Q($this->gettext('outofoffice'))
		);
		return $args;
	}

	function prefs_handler($args)
	{
		// We don't care about anything other than our own section
		if ($args['section'] == 'outofoffice') {
			$blocks = array(
				'autoreply' => array(
					'name' => Q($this->gettext('autoreply_settings'))
				)
			);

			$vacation = $this->user->vacation;

			$input = new html_checkbox(array(
				'id'    => '_autoreply_enabled',
				'name'  => '_autoreply_enabled',
				'size'  => 50,
				'value' => 1
			));
			$blocks['autoreply']['options']['autoreply_enabled'] = array(
				'title'   => html::label('_autoreply_enabled', Q($this->gettext('autoreply_enabled'))),
				'content' => $input->show($vacation->active)
			);

			$input = new html_inputfield(array(
				'id'   => '_autoreply_subject',
				'name' => '_autoreply_subject',
				'size' => 50
			));
			$blocks['autoreply']['options']['autoreply_subject'] = array(
				'title'   => html::label('_autoreply_subject', Q($this->gettext('autoreply_subject'))),
				'content' => $input->show($vacation->subject)
			);

			$input = new html_textarea(array(
				'id'   => '_autoreply_body',
				'name' => '_autoreply_body',
				'cols' => 50,
				'rows' => 15
			));
			$blocks['autoreply']['options']['autoreply_body'] = array(
				'title'   => html::label(array(
						'for' => '_autoreply_body',
						'style' => 'vertical-align: text-top;'
					), Q($this->gettext('autoreply_body'))),
				'content' => $input->show($vacation->body)
			);

			$args['blocks'] = $blocks;
		} else if ($args['section'] == 'password') {
			$blocks = array(
				'passwd' => array(
					'name' => Q($this->gettext('autoreply_settings'))
				)
			);

			// account new password input
			$input = new html_passwordfield(array(
				'id'   => '_curpasswd',
				'name' => '_curpasswd',
				'size' => 50
			));
			$blocks['passwd']['options']['curpasswd'] = array(
				'title'   => html::label('_curpasswd', Q($this->gettext('curpasswd'))),
				'content' => $input->show()
			);

			// account new password input
			$input = new html_passwordfield(array(
				'id'   => '_newpasswd',
				'name' => '_newpasswd',
				'size' => 50
			));
			$blocks['passwd']['options']['newpasswd'] = array(
				'title'   => html::label('_newpasswd', Q($this->gettext('newpasswd'))),
				'content' => $input->show()
			);

			$input = new html_passwordfield(array(
				'id'   => '_confpasswd',
				'name' => '_confpasswd',
				'size' => 50
			));
			$blocks['passwd']['options']['confpasswd'] = array(
				'title'   => html::label('_confpasswd', Q($this->gettext('confpasswd'))),
				'content' => $input->show()
			);
			$args['blocks'] = $blocks;

			$this->rcmail->output->add_gui_object('newpasswd_input', '_newpasswd');
		}
		return $args;
	}

	function prefs_save_handler($args)
	{
		// Again, don't care about other sections.
		if ($args['section'] == 'outofoffice') {

			$autoreply = isset($_POST['_autoreply_enabled']) ? true : false;
			$subject = get_input_value('_autoreply_subject', RCUBE_INPUT_POST);
			$body = get_input_value('_autoreply_body', RCUBE_INPUT_POST);

			// Update the vacation and save
			$vacation = $this->user->vacation;
			$vacation->active = $autoreply;
			$vacation->subject = $subject;
			$vacation->body = $body;

			if ($vacation->modified('active')) {

				$destinations = array();
				$forwarding = $this->user->forwarding;
				$forward_to = $this->user->forward_to;
				$save_copy = $this->user->savecopy;
				
				// this means autoreply forwarding must be setup
				if ($autoreply) {
					$autoreply_email = str_replace('@', '#', $this->user->email);
					$autoreply_email .= '@' . $this->config['autohost'];
					array_push($destinations, $autoreply_email);
				}
				
				if ($forwarding == 'fwd') {
					$forward_to = array_map("trim", explode(',', $forward_to));
					if ($save_copy) {
						$destinations = array_merge(array($this->user->email), $destinations);
						$destinations = array_merge($destinations, $forward_to);
					} else {
						$destinations = array_merge($destinations, $forward_to);
					}
				} else if ($autoreply) {
					$destinations = array_merge(array($this->user->email), $destinations);
				}

				// Update the forward for the user
				$forward = $this->user->forward;

				if (count($destinations) == 0) {
					$forward->delete();
				} else {
					$forward->domain_id = $this->domain_id;
					$forward->source = $this->user->email;
					$forward->destination = implode(',', $destinations);
					$forward->save();
				}
			}

			$vacation->save();


		} else if ($args['section'] == 'password') {
			
			$curpasswd = get_input_value('_curpasswd', RCUBE_INPUT_POST);
			$newpasswd = get_input_value('_newpasswd', RCUBE_INPUT_POST);
			$confpasswd = get_input_value('_confpasswd', RCUBE_INPUT_POST);

			if ($this->user->password != $curpasswd) {
				$this->rcmail->output->show_message('vmail.errbadpasswd','error');
				return $args;
			}
			
			if (!$newpasswd) {
				$this->rcmail->output->show_message('vmail.nopasswd','error');
				return $args;
			}

			if ($newpasswd != $confpasswd) {
				$this->rcmail->output->show_message('vmail.passwdnomatch','error');
				return $args;
			}

			$this->user->password = $newpasswd;
			$this->user->save();

			$this->rcmail->output->show_message('vmail.passwdchanged', 'confirmation');
		}

		return $args;
	}


	/*************************************
	 * Accounts Section          _       *
	 *************************************/
	function accounts_handler()
	{
		$this->set_pagetitle('Accounts');
		$this->set_env('account_create', $this->domain->can_create_account());
		$this->send_template('accounts');
	}

	function add_account_handler()
	{
		$this->aid = 0;
		$this->set_env('account_create', $this->domain->can_create_account());
		if ($this->domain->can_create_account()) {
			$this->set_pagetitle('New Account');
			$this->send_template('accountedit');
		} else {
			$this->error_message('vmail.erracclimit');
			$this->accounts_handler();
		}
	}

	function delete_account_handler()
	{
		$this->aid = (int)get_input_value('_aid', RCUBE_INPUT_GET);
		$this->get_users();

		if ($this->aid > 0 && !in_array($this->aid, array_keys($this->users))) {
			// Show no permission error.
			$this->error_message('vmail.erracclimit');
			return $this->accounts_handler();
		}

		$this->users[$this->aid]->delete();
		unset($this->users[$this->aid]);
		$this->confirmation_message('vmail.accountdeleted', 'confirmation');
		return $this->accounts_handler();
	}

	function edit_account_handler()
	{
		$this->aid = (int)get_input_value('_aid', RCUBE_INPUT_GET);
		$this->set_env('aid', $this->aid);
		$this->set_env('account_create', $this->domain->can_create_account());

		if ($this->aid >= 1) {
			$this->set_pagetitle('Edit Account');
			$this->send_template('accountedit');
		} else {
			$this->error_message('vmail.errnoaid');
			$this->accounts_handler();
		}
	}

	function save_account_handler()
	{
		$this->aid = (int)get_input_value('_aid', RCUBE_INPUT_POST);
		$this->get_users();

		if ($this->aid > 0 && !in_array($this->aid, array_keys($this->users))) {
			// Show no permission error.
			$this->error_message('vmail.erracclimit','error');
			return;
		}

		// Handle getting all the input values from the POST
		$email = strtolower(get_input_value('_email', RCUBE_INPUT_POST));
		$secondmail = strtolower(get_input_value('_secondmail', RCUBE_INPUT_POST));
		$name = get_input_value('_name', RCUBE_INPUT_POST);
		$newpasswd = get_input_value('_newpasswd', RCUBE_INPUT_POST);
		$confpasswd = get_input_value('_confpasswd', RCUBE_INPUT_POST);
		$quota = get_input_value('_quota', RCUBE_INPUT_POST);
		$enabled = isset($_POST['_enabled']);
		$admin = isset($_POST['_admin']);

		// if quota is set to other we need to get the _quotaother field
		if ($quota == 'other') {
			$quota = get_input_value('_quotaother', RCUBE_INPUT_POST);
		}

		// run quota through parse_bytes incase we have a string value.
		$quota = parse_bytes($quota);
		
		// if we still don't have a viable quota use the default quota.
		if (!$quota) {
			$quota = $this->rcmail->config->get('default_quota');
		}

		// forwarding
		$forwarding = get_input_value('_forwarding', RCUBE_INPUT_POST);
		$forward_to = strtolower(get_input_value('_forwardto', RCUBE_INPUT_POST));
		$save_copy = isset($_POST['_savecopy']);

		// autoreply 
		$autoreply = isset($_POST['_autoreply_enabled']);
		$subject = get_input_value('_autoreply_subject', RCUBE_INPUT_POST);
		$body = get_input_value('_autoreply_body', RCUBE_INPUT_POST);

	}

	function accountsave_handler()
	{

		if ($this->aid > 0) {
			$user = $this->users[$this->aid];
		} else {
			$user = new User();
			$user->domain_id = $this->domain_id;
			$user->email = $email . '@' . $this->domain_name;
		}
		$user->name = $name;
		$user->secondary_email = $secondmail;
		$user->quota = $quota;
		$user->enabled = $enabled;
		$user->admin = $admin;
		$this->user = $user;

		if (strpos($email, '@') !== false) {
			$this->rcmail->output->show_message('vmail.errbademail', 'error');
			$this->rcmail->output->set_pagetitle('Edit Account');
			$this->rcmail->output->set_env('focus_field', '_email');
			$this->template = 'accountedit';
			return;
		}

		if ($quota > $this->domain->quota) {
			$this->rcmail->output->show_message('vmail.errbadquota', 'error');
			$this->rcmail->output->set_pagetitle('Edit Account');
			$this->rcmail->output->set_env('focus_field', '_quota');
			$this->template = 'accountedit';
			return;
		}

		if (!$this->aid && !$newpasswd) {
			$this->rcmail->output->show_message('vmail.nopasswd', 'error');
			$this->rcmail->output->set_pagetitle('Edit Account');
			$this->template = 'accountedit';
			return;
		}

		if ($newpasswd && $newpasswd != $confpasswd) {
			$this->rcmail->output->show_message('vmail.passwdnomatch', 'error');
			$this->rcmail->output->set_pagetitle('Edit Account');
			$this->template = 'accountedit';
			return;
		}

		if ($newpasswd) $this->user->password = $newpasswd;
		$this->user->save();

		if (!$this->aid) {
			$this->aid = $this->user->id;
			$this->users[$this->aid] = $this->user;

			// Build uid => email mapping
			foreach ($this->users as $uid => $usr) {
				$uids[$uid] = $usr->email;
			}
			asort($uids);

			// Build new sorted version of the list
			foreach ($uids as $uid => $email) {
				$users[$uid] = $this->users[$uid];
			}
			$this->users = $users;

			$this->rcmail->output->show_message('vmail.accountcreated', 'confirmation');
		} else {
			$this->rcmail->output->show_message('vmail.accountsaved', 'confirmation');
		}

		$vacation = $this->user->vacation;
		$vacation->active = $autoreply;
		$vacation->subject = $subject;
		$vacation->body = $body;

		// calculate the forward destination for the user, if any
		$destinations = array();

		// this means autoreply forwarding must be setup
		if ($autoreply) {
			$autoreply_email = str_replace('@', '#', $this->user->email);
			$autoreply_email .= '@' . $this->config['autohost'];
			array_push($destinations, $autoreply_email);
		}
		
		if ($forwarding == 'fwd') {
			$forward_to = array_map("trim", explode(',', $forward_to));
			if ($save_copy) {
				$destinations = array_merge(array($this->user->email), $destinations);
				$destinations = array_merge($destinations, $forward_to);
			} else {
				$destinations = array_merge($destinations, $forward_to);
			}
		} else if ($autoreply) {
			$destinations = array_merge(array($this->user->email), $destinations);
		}
		$vacation->save();

		// Update the forward for the user
		$forward = $this->user->forward;

		if (count($destinations) == 0) {
			$forward->delete();
		} else {
			$forward->domain_id = $this->domain_id;
			$forward->source = $this->user->email;
			$forward->destination = implode(',', $destinations);
			$forward->save();
		}

		$this->template = 'accountedit';
	}

	/****************************************
	 * Forwards Section                     *
	 ****************************************/
	
	/**
	 * The main forwards handler that displays the forwards list
	 * and the watermark.
	 */
	function forwards_handler()
	{
		$this->set_pagetitle('Forwards');
		$this->send_template('forwards');
	}

	/**
	 * The handler that displays an empty forwards form ready for
	 * adding a new forward to the domain.
	 */
	function add_forward_handler()
	{
		$this->set_pagetitle('New Forward');
		$this->send_template('forwardedit');
	}

	/**
	 * The handler that deletes a forward and the returns to the
	 * main forwards handler
	 */
	function delete_forward_handler()
	{
		$this->fid = get_input_value('_fid', RCUBE_INPUT_GET);
		if (!$this->fid) {
			return;
		}
		$this->get_forwards();

		$forward = $this->forwards[$this->fid];
		if ($forward) {
			$forward->delete();
			$this->update_forward($forward, true);
			$this->confirmation_message('vmail.forwarddeleted');
		} else {
			$this->error_message('vmail.errdeleteforward');
		}

		// The rest of the process is the same as the default page
		$this->forwards_handler();
	}

	function edit_forward_handler()
	{
		$this->fid = get_input_value('_fid', RCUBE_INPUT_GET);
		$this->get_forwards();
		$this->forward = $this->forwards[$this->fid];

		// Check to see if someone has entered an invalid id
		if (!$this->forward) {
			$this->error_message('vmail.errnoforward');
			$this->forwards_handler();
		}

		$this->set_env('fid', $this->fid);
		$this->set_pagetitle('Edit Forward');
		$this->send_template('forwardedit');
	}

	function save_forward_handler()
	{
		// First things first, set the page title
		$this->rcmail->output->set_pagetitle('Edit Forward');

		// Get the POST values for the forward
		$source = strtolower(get_input_value('_source', RCUBE_INPUT_POST));
		$catchall = get_input_value('_catchall', RCUBE_INPUT_POST);
		foreach (get_input_value('_destination', RCUBE_INPUT_POST) as $d) {
			$destinations[] = strtolower($d);
		}

		// If this is a catchall then we want to disregard the source
		if ($catchall) $source = '';

		// Create the forward now so the users input details don't
		// disappear incase of an error
		$this->forward = new Forward();
		$this->forward->domain_id = $this->domain_id;
		$this->forward->source = $source . '@' . $this->domain_name;
		$this->forward->destinations = $destinations;

		// We want to make sure there aren't any invalid characters
		// in the forward source local-part.
		// TODO: make this RFC compliant
		if (strpos($source, '@') !== false) {
			$this->error_message('vmail.errbadsource');
			$this->edit_forward_handler();
			return;
		}

		// Get the forwards and the users
		$this->get_forwards();

		// Check to see if the forward clashes with a user name or not
		if (in_array($forward->source, $this->usernames)) {
			$this->error_message('vmail.erraccexists');
		}

		// We are good to save
		$this->forward->save();

		// Update the forwards list
		$this->update_forward($this->forward);
		$this->confirmation_message('vmail.forwardsaved');

		// Display the edit page again
		$this->set_env('fid', $this->fid);
		$this->send_template('forwardedit');
	}

	/******************************************************************
	 * Helper methods                                                 *
	 ******************************************************************/
	function confirmation_message($message)
	{
		$this->rcmail->output->show_message($message, 'confirmation');
	}

	function error_message($message)
	{
		$this->rcmail->output->show_message($message, 'error');
	}

	function send_template($template)
	{
		$this->rcmail->output->send("vmail.$template");
	}

	function set_env($key, $value)
	{
		$this->rcmail->output->set_env($key, $value);
	}

	function set_pagetitle($title)
	{
		$this->rcmail->output->set_pagetitle($title);
	}

	function get_forwards($domain = null)
	{
		$_forwards = (!$this->forwards) ? $this->domain->forwards : $this->forwards;

		if (!$this->users) {
			$this->users = $this->domain->users;
			foreach ($this->users as $user) {
				$this->usernames[] = $user->email;
			}
		}

		usort($_forwards, 'fwdcmp');

		$i = 1;
		foreach ($_forwards as $forward) {
			// Give the forward an id if it hasn't already got one
			if (!$forward->id) $forward->id = md5($forward->source);

			// Skip the forward if needs be
			if ($this->skip_forward($forward)) {
				continue;
			}

			// Store the forward for later use
			$this->forwards[$forward->id] = $forward;

			// Save the forward row ready for display
			$forwards[] = $this->forward_to_row($forward);
		}

		return $forwards;
	}

	/**
	 * See if a Forward should be skipped from being displayed in the
	 * forwards list.
	 * @param forward The forward to check to see if it should be skipped
	 */
	function skip_forward($forward)
	{
		// Check to see if this is a mailing list forward
		foreach ($forward->destinations as $destination) {
			// FIXME: This is still using a hardcoded ukplc.net
			if (strpos($destination, '@lists.ukplc.net') !== false) {
				return true;
			}
		}

		// Look and see if this forward belongs to a user
		if (in_array($forward->source, $this->usernames)) {
			return true;
		}
	}

	/**
	 * Convert a forward into a row ready for display in a table or list
	 */
	function forward_to_row($forward)
	{
		// Format the forward for display in the list
		foreach ($forward->keys as $col) {
			$row["vmail.$col"] = $forward->$col;
		}
		
		// Use the Any Address text if this is a catch all
		if ($forward->catchall) {
			$row['vmail.source'] = $this->gettext('anyaddress');
		}

		// Set the forward id
		$row['vmail.id'] = $forward->id;

		return $row;
	}

	function update_forward($forward, $remove = false)
	{
		$this->fid = null;

		// Sort out the local forwards store now, potentially 
		// having to remove the new forward.
		$i = 1;
		foreach ($this->forwards as $f) {
			if ($f->source == $forward->source) {
				if (!$remove) {
					$forwards[$forward->id] = $forward;
					$this->fid = $forward->id;
				} else {
					$this->fid = -1;
				}
			} else {
				$forwards[$f->id] = $f;
			}
		}

		// This is a new forward so need to add it to the list
		if (!$this->fid) {
			$forward->id = md5($forward->source);
			$forwards[$forward->id] = $forward;
			$this->fid = $forward->id;
		}

		// Sort the list and then set it as the active one
		uasort($forwards, 'fwdcmp');
		$this->forwards = $forwards;
	}

	function get_users($domain = null)
	{
		$_users = (!$this->users) ? $this->domain->users : array_values($this->users);
		$store = !$this->users;

		foreach ($_users as $user) {
			if ($store) {
				$this->usernames[] = $user->email;
				$this->users[$user->id] = $user;
			}
			$users[] = $this->user_to_row($user);
		}
		return $users;
	}

	function user_to_row($user)
	{
		$quota = ($this->aid == $user->id) ? 'quota_sel' : 'quota';
		$class = ($user->id == $this->user->id) ? 'current-user' : '';
		$class .= (!$user->enabled) ? ' disabled' : '';

		return array(
			'user_id'    => $user->id,
			'user_email' => $user->email,
			'user_quota' => html::div('quota_wrapper',
				quota_bar($user->usage, $user->quota, "plugins/vmail/skins/default/quota.gif")),
			'class'      => $class
		);
	}

	/******************************************************************
	 * HTML Handlers                                                  *
	 ******************************************************************/
	function accountslist_html($attrib)
	{
		$users = $this->get_users();

		$limit = $this->domain->account_limit;
		$limit = ($limit > 0) ? $limit : $this->gettext('unlimited');

		// Set up the columns to display.
		$cols = array(
			'user_email',
			'user_quota'
		);

		$this->rcmail->output->include_script('list.js');
		$this->rcmail->output->add_gui_object('accountslist', 'accounts-table');
		return raw_table_output($attrib, $users, $cols, 'user_id');
	}

	function accountsquota_html()
	{
		return quota_bar($this->domain->usage, $this->domain->quota);
	}

	function accounts_count_html()
	{
		$user_count =  count($this->get_users());
		$limit = $this->domain->account_limit;
		$limit = ($limit > 0) ? $limit : $this->gettext('unlimited');

		$out = '<span id="accounts-count">(';
		$out .= $user_count .' / ' . $limit;
		$out .= ')</span>';
		return $out;
	}

	function accounteditform_html()
	{
		$out = $this->rcmail->output->form_tag(array(
			'id' => 'accounteditform',
			'name' => 'accounteditform',
			'method' => 'post',
			'action' => './?_task=settings&_action=plugin.save-account'
		));
		$this->rcmail->output->add_gui_object('account_form', 'accounteditform');
		$hiddenfields = new html_hiddenfield(array(
			'name'  => '_aid',
			'value' => $this->aid
		));
		$out .= $hiddenfields->show();

		$table = new html_table(array('cols' => 2));

		if (!$this->aid) {
			$account = new User();
			// account email input
			$input = new html_inputfield(array(
				'id'   => '_email',
				'name' => '_email',
				'size' => 50
			));
			$table->add('title', $this->form_label('_email', 'email'));
			$table->add(null, $input->show($account->email) . '@' . $this->domain_name);
			$this->rcmail->output->add_gui_object('email_input', '_email');
		} else {
			$account = ($this->user->id == $this->aid) ? $this->user : $this->users[$this->aid];
		}

		// account name input
		$input = new html_inputfield(array(
			'id'   => '_name',
			'name' => '_name',
			'size' => 50
		));
		$table->add('title', $this->form_label('_name', 'name'));
		$table->add(null, $input->show($account->name));

		// account secondary email input
		$input = new html_inputfield(array(
			'id'   => '_secondmail',
			'name' => '_secondmail',
			'size' => 50
		));
		$table->add('title', $this->form_label('_secondmail', 'secondmail'));
		$table->add(null, $input->show($account->secondary_email));

		// account new password input
		$input = new html_passwordfield(array(
			'id'   => '_newpasswd',
			'name' => '_newpasswd',
			'size' => 50
		));
		$table->add('title', $this->form_label('_newpasswd', 'newpasswd'));
		$table->add(null, $input->show());

		// account confirm password input
		$input = new html_passwordfield(array(
			'id'   => '_confpasswd',
			'name' => '_confpasswd',
			'size' => 50
		));
		$table->add('title', $this->form_label('_confpasswd', 'confpasswd'));
		$table->add(null, $input->show());

		// account quota input
		$input = new html_select(array(
			'id'   => '_quota',
			'name' => '_quota'
		));

		// calculate quota options
		$domain_quota = $this->domain->quota;
		$values = array(
			$domain_quota * 0.05,
			$domain_quota * 0.10,
			$domain_quota * 0.25,
			$domain_quota * 0.5,
			$domain_quota * 0.75,
			$domain_quota,
			'other'
		);
		function format($n) {
			return (is_numeric($n)) ? show_bytes($n) : rcube_label('vmail.'.$n);
		}
		$options = array_map("format", $values);

		$input->add($options, $values);
		$table->add('title', $this->form_label('_quota', 'quota'));

		$quota = ($account->id) ? $account->fget('quota') : show_bytes($values[count($values) -2]);
		if (!in_array($quota, $options)) {
			$quotaother = $quota;
			$quota = $this->gettext('other');
		}
		$table->add(null, $input->show($quota));
		$this->rcmail->output->add_gui_object('quota_input', '_quota');

		// account other quota input
		$table->add(null, '&nbsp;');
		$input = new html_inputfield(array(
			'id'   => '_quotaother',
			'name' => '_quotaother',
			'size' => 50
		));
		$table->add(null, $input->show($quotaother));
		$this->rcmail->output->add_gui_object('quotaother_input', '_quotaother');

		// account enabled input
		$input = new html_checkbox(array(
			'id'    => '_enabled',
			'name'  => '_enabled',
			'value' => 1
		));
		$table->add('title', $this->form_label('_enabled', 'enabled'));
		$table->add(null, $input->show(($account->id) ? $account->enabled : true));
		
		// account admin input
		$attr = array(
			'id'    => '_admin',
			'name'  => '_admin',
			'value' => 1
		);
		if (($this->admin_count == 1 && $account->admin) || get_user_part($account->email) == 'postmaster') {
			$attr['disabled'] = 'yes';
			$hiddenfields = new html_hiddenfield(array(
				'name'  => '_admin',
				'value' => 1
			));
			$out .= $hiddenfields->show();
		}
		$input = new html_checkbox($attr);
		$table->add('title', $this->form_label('_admin', 'admin'));
		$table->add(null, $input->show($account->admin));

		$table->add(null, '&nbsp;');
		$table->add(null, '&nbsp;');

		$table->add('header', $this->gettext('forwarding'));
		$table->add_row();

		$tmp = '<label>';
		$input = new html_radiobutton(array(
			'id'    => '_stdforward',
			'name'  => '_forwarding',
			'value' => 'std'
		));
		$tmp .= $input->show($account->forwarding);
		$tmp .= $this->gettext('stdforward');
		$tmp .= '</label>';
		$table->add(array('colspan' => 2), $tmp);
		$table->add_row();
		$this->rcmail->output->add_gui_object('stdforward_input', '_stdforward');

		$tmp = '<label>';
		$input = new html_radiobutton(array(
			'id'    => '_fwdforward',
			'name'  => '_forwarding',
			'value' => 'fwd'
		));
		$tmp .= $input->show($account->forwarding);
		$tmp .= $this->gettext('fwdforward');
		$input = new html_inputfield(array(
			'id'   => '_forwardto',
			'name' => '_forwardto',
			'size' => 50
		));
		$tmp .= $input->show($account->forwardto);
		$tmp .= '</label>';
		$table->add(array('colspan' => 2), $tmp);
		$table->add_row();
		$this->rcmail->output->add_gui_object('fwdforward_input', '_fwdforward');
		$this->rcmail->output->add_gui_object('forwardto_input', '_forwardto');

		$tmp = '<label style="margin-left: 20px;">';
		$input = new html_checkbox(array(
			'name' => '_savecopy',
			'value' => '1'
		));
		$tmp .= $input->show($account->savecopy);
		$tmp .= $this->gettext('savecopy');
		$tmp .= '</label>';
		$this->rcmail->output->add_gui_object('savecopy_input', '_savecopy');

		$table->add(array('colspan' => 2), $tmp);
		$table->add_row();

		$table->add(null, '&nbsp;');
		$table->add(null, '&nbsp;');

		if (get_user_part($account->email) != 'postmaster') {

			$vacation = $account->vacation;

			$table->add('header', $this->gettext('outofoffice'));
			$table->add_row();

			// autoreply enabled input
			$input = new html_checkbox(array(
				'id'    => '_autoreply_enabled',
				'name'  => '_autoreply_enabled',
				'value' => 1
			));
			$table->add('title', $this->form_label('_autoreply_enabled', 'enabled'));
			$table->add(null, $input->show($vacation->active));

			// autoreply subject input
			$input = new html_inputfield(array(
				'id'   => '_autoreply_subject',
				'name' => '_autoreply_subject',
				'size' => 50
			));
			$table->add('title', $this->form_label('_autoreply_subject', 'subject'));
			$table->add(null, $input->show($vacation->subject));

			// autoreply subject input
			$input = new html_textarea(array(
				'id'   => '_autoreply_body',
				'name' => '_autoreply_body',
				'cols' => 50,
				'rows' => 10
			));
			$table->add('title', $this->form_label('_autoreply_body', 'autoreply_body'));
			$table->add(null, $input->show($vacation->body));

		}

		$out .= $table->show();
		$out .= '</form>';

		// delete button
		$attr =  array(
			'id'    => '_delete_acc',
			'class' => 'button',
			'name'  => '_action',
			'style' => 'margin-right: 0.5em',
			'type'  => 'button',
			'value' => Q(rcube_label('delete'))
		);

		if ($this->aid != null && get_user_part($account->email) != 'postmaster' && $this->aid != $this->user->id) {
			$this->set_env('can_delete_user', true);
		} else {
			$this->set_env('can_delete_user', false);
		}
		return $out;
	}

	function form_label($input_id, $label)
	{
		$label = Q($this->gettext($label));
		return sprintf('<label for="%s"><b>%s:</b></label>', $input_id, $label);
	}

	function forwardslist_html($attrib)
	{
		$forwards = $this->get_forwards();

		// Set up the columns to display.
		$cols = array('vmail.source');

		$this->rcmail->output->include_script('list.js');
		$this->rcmail->output->add_gui_object('forwards_list', 'forwards-table');
		return rcube_table_output($attrib, $forwards, $cols, 'vmail.id');
	}

	function forwardeditform_html()
	{
		$title = Q($this->gettext(($this->fid) ? 'editforward' : 'newforward'));
		$out = $this->rcmail->output->form_tag(array(
			'id' => 'forwardeditform',
			'name' => 'forwardeditform',
			'method' => 'post',
			'action' => './?_task=settings&_action=plugin.save-forward'
		));
		$this->rcmail->output->add_gui_object('forward_form', 'forwardeditform');
		$hiddenfields = new html_hiddenfield(array(
			'name'  => '_fid',
			'value' => $this->fid
		));
		$out .= $hiddenfields->show();

		$table = new html_table(array('cols' => 3));

		$forward = ($this->forward) ? $this->forward : $this->forwards[$this->fid];
		$source = get_user_part($forward->source);

		// forward catchall checkbox
		$input = new html_checkbox(array(
			'id'    => '_catchall',
			'name'  => '_catchall',
			'value' => 1
		));
		$table->add('title', $this->form_label('_catchall', 'catchall'));
		$table->add(null, $input->show($forward->catchall));
		$this->rcmail->output->add_gui_object('catchall_input', '_catchall');
		$table->add_row();

		// forward source input
		$input = new html_inputfield(array(
			'id'   => '_source',
			'name' => '_source',
			'size' => 50
		));
		$table->add('title', $this->form_label('_source', 'source'));
		$table->add(null, $input->show($source) . '@' . $this->domain_name);
		$this->rcmail->output->add_gui_object('source_input', '_source');
		$table->add_row();

		// Add a break before the destinations table
		$table->add(null, '&nbsp;');
		$table->add_row();

		// Add a header
		$table->add('header', $this->gettext('destinations'));
		$table->add_row();

		// Add the help message
		$table->add(array('colspan'=>3), '<p style="width: 600px; font-style: italic">' . $this->gettext('helpdestinations') . '</p>');
		$table->add_row();
		
		// Set up the destinations to display.
		$i = 0;

		// Create the destinations
		$destinations = ($forward->destinations) ? $forward->destinations : array('');

		// Loop over creating the form elements for them
		foreach ($destinations as $destination) {
			$table->set_row_attribs(array('class' => 'dst-row'));

			// Create the input field, the [] at the end is important for
			// PHP to store the values as an array in the post-back.
			$input = new html_inputfield(array(
				'name' => "_destination[]",
				'class' => 'dst-input',
				'size' => 80
			));
			$table->add(array('colspan'=>2), $input->show($destination));

			// Create the Delete button, need to disable this if there is
			// only one destination otherwise silly users might
			// accidentally destroy a forward.
			$attribs = array(
				'class' => 'button dst-delete-btn',
				'style' => 'margin-right: 0.5em',
				'type'  => 'button',
				'value' => Q(rcube_label('delete'))
			);

			if (count($destinations) == 1) {
				$attribs['class'] .= ' disabled';
				$attribs['disabled'] = true;
			}

			$del_btn = new html_inputfield($attribs);
			$table->add(null, $del_btn->show());

			$add_btn = new html_inputfield(array(
				'class' => 'button dst-add-btn',
				'style' => 'margin-right: 0.5em',
				'type'  => 'button',
				'value' => Q(rcube_label('vmail.add'))
			));
			$table->add(null, $add_btn->show());
			$table->add_row();
		}

		$out .= $table->show();
		$out .= '</form>';
		return $out;
	}
}
?>
