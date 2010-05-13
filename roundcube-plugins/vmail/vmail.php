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

require 'lib/funcs.inc';
require 'lib/accounts.class.inc';
require 'lib/domains.class.inc';
require 'lib/forwards.class.inc';

class vmail extends rcube_plugin
{
	public $task = 'settings';

	function init()
	{
		$this->rcmail = &rcmail::get_instance();
		$this->load_config();
		$this->add_texts('localization/', array('vmail'));

		// Setup the database access
		DBBase::$vmail = $this;

		// Get the current user
		$user = $this->rcmail->user;
		$this->account = Account::get_by_username($user->data['username']);

		// Set up modifying the out of office message via the preferences
		// tab in settings.
		$this->add_hook('list_prefs_sections',
			array($this, 'listprefs_handler'));
		$this->add_hook('user_preferences',
			array($this, 'prefs_handler'));
		$this->add_hook('save_preferences',
			array($this, 'prefs_save_handler'));

		// Get the domain information from the database.
		$this->domain = $this->account->get_domain();
		$this->domain_id = $this->domain->id;
		$this->domain_name = $this->domain->get('domain');

		// If the user isn't an admin we can't continue.
		if (!$this->account->is_admin) return;

		// Set the id of the current account being editing to 0.
		$this->aid = 0;

		$pos = strrpos($user->data['username'], '@');
		$this->username = substr($user->data['username'], 0, $pos);
		$this->rcmail->output->set_env('user', $user->data['username']);

		// Finish setting up the plugin
		$this->include_script('vmail.js');
		$this->include_stylesheet('vmail.css');

		// Register the accounts section
		$this->register_action('plugin.accounts',
			array($this, 'accounts_handler'));
		$this->register_handler('plugin.accountslist',
			array($this, 'accountslist_html'));
		$this->register_handler('plugin.accounteditform',
			array($this, 'accounteditform_html'));

		// Register the forwards section
		$this->register_action('plugin.forwards',
			array($this, 'forwards_handler'));
		$this->register_handler('plugin.forwardslist',
			array($this, 'forwardslist_html'));
		$this->register_handler('plugin.forwardeditform',
			array($this, 'forwardeditform_html'));
	}

	function listprefs_handler($args)
	{
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
		if ($args['section'] != 'outofoffice') return $args;


		$blocks = array(
			'autoreply' => array(
				'name' => Q($this->gettext('autoreply_settings'))
			)
		);

		$input = new html_checkbox(array(
			'id'    => '_autoreply_enabled',
			'name'  => '_autoreply_enabled',
			'size'  => 50,
			'value' => 1
		));
		$blocks['autoreply']['options']['autoreply_enabled'] = array(
			'title'   => html::label('_autoreply_enabled', Q($this->gettext('autoreply_enabled'))),
			'content' => $input->show($this->account->get('autoreply'))
		);

		$input = new html_inputfield(array(
			'id'   => '_autoreply_subject',
			'name' => '_autoreply_subject',
			'size' => 50
		));
		$blocks['autoreply']['options']['autoreply_subject'] = array(
			'title'   => html::label('_autoreply_subject', Q($this->gettext('autoreply_subject'))),
			'content' => $input->show($this->account->get('autoreply_subject'))
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
			'content' => $input->show($this->account->get('autoreply_body'))
		);

		$args['blocks'] = $blocks;
		return $args;
	}

	function prefs_save_handler($args)
	{
		// Again, don't care about other sections.
		if ($args['section'] != 'outofoffice') return;

		$autoreply = isset($_POST['_autoreply_enabled']) ? true : false;
		$subject = get_input_value('_autoreply_subject', RCUBE_INPUT_POST);
		$body = get_input_value('_autoreply_body', RCUBE_INPUT_POST);

		$this->account->set('autoreply', $autoreply);
		$this->account->set('autoreply_subject', $subject);
		$this->account->set('autoreply_body', $body);
		$this->account->save();

		return $args;
	}

	function accounts_handler()
	{
		$this->rcmail->output->set_pagetitle('Accounts');
		$this->template = 'accounts';
		if ($action = get_input_value('_act', RCUBE_INPUT_GPC)) {
			$this->aid = (int) get_input_value('_aid', RCUBE_INPUT_GET);

			if ($action == 'del') {
				if ($this->can_edit_account($this->aid)) {
					$account = new Account($this->aid, false);
					$account->delete();
					$this->rcmail->output->show_message('vmail.accountdeleted', 'confirmation');
				}

			} else if ($action == 'edit') {
				if ($this->aid >= 1) {
					$this->rcmail->output->set_pagetitle('Edit Account');
					$this->template = 'accountedit';
				} else {
					$this->rcmail->output->show_message('vmail.errnoaid', 'error');
				}

			} else if ($action == 'new') {
				$this->aid = 0;
				if ($this->domain->can_create_account()) {
					$this->rcmail->output->set_pagetitle('New Account');
					$this->template = 'accountedit';
				} else {
					$this->rcmail->output->show_message('vmail.erracclimit', 'error');
				}

			} else if ($action == 'save') {
				$this->accountsave_handler();
			}
		}
		$this->rcmail->output->set_env('aid', $this->aid);
		$this->rcmail->output->set_env('account_create', $this->domain->can_create_account());
		$this->rcmail->output->send('vmail.' . $this->template);
	}

	function accountsave_handler()
	{
		$this->aid = (int)get_input_value('_aid', RCUBE_INPUT_POST);

		if (!$this->domain->can_edit_account($this->aid)) {
			// Show no permission error.
			$this->rcmail->output->show_message('vmail.erracclimit','error');
			return;
		}

		$email = strtolower(get_input_value('_email', RCUBE_INPUT_POST));
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

		$account = new Account($this->aid, true);
		$account->set('domain_id', $this->domain_id);
		$account->set('email', $email);
		$account->set('name', $name);
		$account->set('quota', $quota);
		$account->set('enabled', $enabled);
		$account->set('admin', $admin);
		$account->set('forwarding', $forwarding);
		$account->set('forwardto', $forward_to);
		$account->set('savecopy', $save_copy);
		$account->set('autoreply', $autoreply);
		$account->set('autoreply_subject', $subject);
		$account->set('autoreply_body', $body);
		$this->account = $account;

		if (strpos($email, '@') !== false) {
			$this->rcmail->output->show_message('vmail.errbademail', 'error');
			$this->rcmail->output->set_pagetitle('Edit Account');
			$this->rcmail->output->set_env('focus_field', '_email');
			$this->template = 'accountedit';
			return;
		}

		if ($quota > $this->domain->get('quota')) {
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

		if ($newpasswd) $this->account->set('password', $newpasswd);
		$this->account->save();

		if (!$this->aid) {
			// Probably want to send the welcome email at this point.
			createmaildir($this->account->get('email') . '@' . $this->domain_name);

			$this->aid = $this->account->id;
			$this->rcmail->output->show_message('vmail.accountcreated', 'confirmation');
		} else {
			$this->rcmail->output->show_message('vmail.accountsaved', 'confirmation');
		}

		$this->template = 'accountedit';
	}

	function forwards_handler()
	{
		$this->rcmail->output->set_pagetitle('Forwards');
		$this->template = 'forwards';
		if ($action = get_input_value('_act', RCUBE_INPUT_GPC)) {
			$this->fid = (int) get_input_value('_fid', RCUBE_INPUT_GET);
			if ($action == 'del') {
				$this->forwarddel_handler();
			} else if ($action == 'edit') {
				$this->rcmail->output->set_pagetitle('Edit Forward');
				$this->template = 'forwardedit';

			} else if ($action == 'new') {
				$this->rcmail->output->set_pagetitle('New Forward');
				$this->template = 'forwardedit';

			} else if ($action == 'save') {
				$this->forwardsave_handler();

			}
		}
		$this->rcmail->output->set_env('act', $action);
		$this->rcmail->output->set_env('fid', $this->fid);
		$this->rcmail->output->send('vmail.' . $this->template);
	}

	function forwarddel_handler()
	{
		if (!$this->can_edit_forward($this->fid)) {
			return;
		}

		$forward = new Forward($this->fid, false);
		$forward->delete();

		$this->rcmail->output->show_message('vmail.forwarddeleted', 'confirmation');
	}

	function forwardsave_handler()
	{
		$this->fid = (int)get_input_value('_fid', RCUBE_INPUT_POST);
		
		$source = strtolower(get_input_value('_source', RCUBE_INPUT_POST));
		$catchall = get_input_value('_catchall', RCUBE_INPUT_POST);
		$destination = strtolower(get_input_value('_destination', RCUBE_INPUT_POST));

		if ($catchall) $source = '';
		$this->forward = new Forward($this->fid, false);
		$this->forward->set('domain_id', $this->domain_id);
		$this->forward->set('source', $source . '@' . $this->domain_name);
		$this->forward->set('destination', $destination);

		$account = Account::get_by_username($source . '@' . $this->domain_name);
		if ($account->id) {
			$this->rcmail->output->show_message('vmail.erraccexists', 'error');
			$this->template = 'forwardedit';
			return;
		}

		if (strpos($source, '@') !== false) {
			$this->rcmail->output->show_message('vmail.errbadsource', 'error');
			$this->rcmail->output->set_env('focus_field', '_source');
			$this->template = 'forwardedit';
			return;
		}

		$res = $this->forward->save();
		
		// Check for errors
		if ($res == 1) {
			$this->rcmail->output->show_message('vmail.forwardexists', 'error');
			return;
		} else if ($res == 2) {
			$this->rcmail->output->show_message('vmail.dberror', 'error');
			return;
		}

		if (!$this->fid) {
			$this->fid = $forward->id;
			$this->rcmail->output->show_message('vmail.forwardcreated', 'confirmation');
		} else {
			$this->rcmail->output->show_message('vmail.forwardsaved', 'confirmation');
		}
		$this->template = 'forwardedit';
	}

	/******************************************************************
	 * Helper methods                                                 *
	 ******************************************************************/
	function get_forwards($domain = null)
	{
		$db = DBBase::get_db();
		if (!$domain) {
			$sql  = "SELECT * FROM forwardings ";
			$sql .= "WHERE domain_id = %d AND ";
			$sql .= "source NOT IN (SELECT email FROM users) AND ";
			$sql .= "destination NOT LIKE '%@lists.ukplc.net' ORDER BY source;";
			$domain = $this->domain_id;
		} else {
			$sql  = "SELECT f.* FROM forwardings";
			$sql .= " f INNER JOIN forwardings f ON f.domain_id = d.id";
			$sql .= " WHERE d.domain = %d";
			$sql .= " AND source NOT IN (SELECT email FROM users)";
			$sql .= " AND destination NOT LIKE '%@lists.ukplc.net' ORDER BY source;";
		}
		$sql = str_replace('%d', $db->quote($domain), $sql);
		$res = $db->query($sql);

		while ($row = $db->fetch_assoc($res)) {
			foreach ($row as $col => $val) {
				$row['vmail.' . $col] = $val;
				unset($row[$col]);
			}
			if ($row['vmail.source'] == '@' . $this->domain_name) {
				$row['vmail.source'] = $this->gettext('anyaddress');
			}
			$forwards[] = $row;
		}
		return $forwards;
	}

	function can_edit_account($aid)
	{
		return Account::can_edit($this->domain_id, $aid);
	}

	function can_edit_forward($fid)
	{
		if ($aid == -1 || $aid == 0) return true;
		$db = DBBase::get_db();
		$sql = "SELECT domain_id FROM forwardings WHERE id = %i";
		$sql = str_replace('%i', $db->quote($fid), $sql);
		$res = $db->query($sql);
		if ($row = $db->fetch_array($res))
			return $row[0] == $this->domain_id;
		return false;
	}

	function get_domain_id($domain)
	{
		$db = DBBase::get_db();
		$sql = "SELECT id FROM domains WHERE domain = %d";
		$sql = str_replace('%d', $db->quote($domain), $sql);
		$res = $db->query($sql);
		if ($row = $db->fetch_array($res))
			return intval($row[0]);
		return 0;
	}

	/******************************************************************
	 * HTML Handlers                                                  *
	 ******************************************************************/
	function accountslist_html()
	{
		$accounts = $this->domain->get_accounts();
		$accounts = format_accounts_with_usage($accounts);

		$limit = $this->domain->get('account_limit');
		$limit = ($limit > 0) ? $limit : $this->gettext('unlimited');

		// Set up the columns to display.
		$cols = array(
			'vmail.email',
			'vmail.quota',
			'vmail.enabled'
		);

		$out = rcube_table_output(array(
			'cols'        => 3,
			'cellpadding' => 0,
			'cellspacing' => 0,
			'class'       => 'records-table',
			'id'          => 'accounts-table'),
			$accounts, $cols, 'vmail.id');
		$out .= '<div id="domain-quota">';
		$out .= '<div id="domain-accounts">';
		$out .= $this->gettext('accounts') . ': ' . count($accounts) . ' / ' . $limit;
		$out .= '</div>';
		$out .= '<div id="domain-usage">';
		$out .= $this->gettext('quota') . ': ' . show_bytes($this->domain->get_usage()) . ' / ' . show_bytes($this->domain->get('quota'));
		$out .= '</div>';
		$out .= '</div>';
		$this->rcmail->output->include_script('list.js');
		$this->rcmail->output->add_gui_object('accountslist', 'accounts-table');
		return $out;
	}

	function accounteditform_html()
	{
		$title = Q($this->gettext(($this->aid) ? 'editaccount' : 'newaccount'));
		$out = '<div id="account-title" class="boxtitle">' . $title . '</div>';
		$out .= '<div class="boxcontent">';
		$out .= $this->rcmail->output->form_tag(array(
			'id' => 'accounteditform',
			'name' => 'accounteditform',
			'method' => 'post',
			'action' => './?_task=settings&_action=plugin.accounts&_act=save'
		));
		$this->rcmail->output->add_gui_object('account_form', 'accounteditform');
		$hiddenfields = new html_hiddenfield(array(
			'name'  => '_aid',
			'value' => $this->aid
		));
		$out .= $hiddenfields->show();

		$table = new html_table(array('cols' => 2));
		$account = ($this->account->id == $this->aid) ? $this->account : new Account($this->aid);

		if (!$this->aid) {
			// account email input
			$input = new html_inputfield(array(
				'id'   => '_email',
				'name' => '_email',
				'size' => 50
			));
			$table->add('title', $this->form_label('_email', 'email'));
			$table->add(null, $input->show($account->get('email')) . '@' . $this->domain_name);
			$this->rcmail->output->add_gui_object('email_input', '_email');
		}

		// account name input
		$input = new html_inputfield(array(
			'id'   => '_name',
			'name' => '_name',
			'size' => 50
		));
		$table->add('title', $this->form_label('_name', 'name'));
		$table->add(null, $input->show($account->get('name')));

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
		$domain_quota = $this->domain->get('quota');
		$values = array(
			$domain_quota * 0.05,
			$domain_quota * 0.1,
			$domain_quota * 0.2,
			$domain_quota * 0.4,
			$domain_quota * 0.7,
			$domain_quota,
			'other'
		);
		function format($n) {
			return (is_numeric($n)) ? show_bytes($n) : rcube_label('vmail.'.$n);
		}
		$options = array_map("format", $values);

		$input->add($options, $values);
		$table->add('title', $this->form_label('_quota', 'quota'));

		$quota = $account->fget('quota');
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
		$table->add(null, $input->show($account->get('enabled')));
		
		// account admin input
		$attr = array(
			'id'    => '_admin',
			'name'  => '_admin',
			'value' => 1
		);
		if (($this->admin_count == 1 && $account->get('admin')) || get_user_part($account->get('email')) == 'postmaster') {
			$attr['disabled'] = 'yes';
			$hiddenfields = new html_hiddenfield(array(
				'name'  => '_admin',
				'value' => 1
			));
			$out .= $hiddenfields->show();
		}
		$input = new html_checkbox($attr);
		$table->add('title', $this->form_label('_admin', 'admin'));
		$table->add(null, $input->show($account->get('admin')));

		$table->add(null, '&nbsp;');
		$table->add(null, '&nbsp;');

		$table->add('title', sprintf("<b><u>%s</u></b>", $this->gettext('forwarding')));
		$table->add_row();

		$tmp = '<label>';
		$input = new html_radiobutton(array(
			'id'    => '_stdforward',
			'name'  => '_forwarding',
			'value' => 'std'
		));
		$tmp .= $input->show($account->get('forwarding'));
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
		$tmp .= $input->show($account->get('forwarding'));
		$tmp .= $this->gettext('fwdforward');
		$input = new html_inputfield(array(
			'id'   => '_forwardto',
			'name' => '_forwardto',
			'size' => 50
		));
		$tmp .= $input->show($account->get('forwardto'));
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
		$tmp .= $input->show($account->get('savecopy'));
		$tmp .= $this->gettext('savecopy');
		$tmp .= '</label>';
		$this->rcmail->output->add_gui_object('savecopy_input', '_savecopy');

		$table->add(array('colspan' => 2), $tmp);
		$table->add_row();

		$table->add(null, '&nbsp;');
		$table->add(null, '&nbsp;');

		$table->add('title', sprintf("<b><u>%s</u></b>", $this->gettext('outofoffice')));
		$table->add_row();

		// autoreply enabled input
		$input = new html_checkbox(array(
			'id'    => '_autoreply_enabled',
			'name'  => '_autoreply_enabled',
			'value' => 1
		));
		$table->add('title', $this->form_label('_autoreply_enabled', 'enabled'));
		$table->add(null, $input->show($account->get('autoreply')));

		// autoreply subject input
		$input = new html_inputfield(array(
			'id'   => '_autoreply_subject',
			'name' => '_autoreply_subject',
			'size' => 50
		));
		$table->add('title', $this->form_label('_autoreply_subject', 'subject'));
		$table->add(null, $input->show($account->fget('autoreply_subject')));

		// autoreply subject input
		$input = new html_textarea(array(
			'id'   => '_autoreply_body',
			'name' => '_autoreply_body',
			'cols' => 50,
			'rows' => 10
		));
		$table->add('title', $this->form_label('_autoreply_body', 'autoreply_body'));
		$table->add(null, $input->show($account->fget('autoreply_body')));

		$out .= $table->show();
		$out .= '</form>';
		$out .= '<p>';

		// delete button
		$attr =  array(
			'id'    => '_delete_acc',
			'class' => 'button',
			'name'  => '_action',
			'style' => 'margin-right: 0.5em',
			'type'  => 'button',
			'value' => Q(rcube_label('delete'))
		);
		if (!$this->aid || get_user_part($account->get('email')) == 'postmaster') {
			$attr['disabled'] = true;
			$attr['style'] .= '; color: gray;';
		}
		$input = new html_inputfield($attr);
		$out .= $input->show();
		$this->rcmail->output->add_gui_object('del_account', '_delete_acc');

		// save button
		$input = new html_inputfield(array(
			'id'    => '_save_acc',
			'class' => 'button mainaction',
			'name'  => '_action',
			'type'  => 'button',
			'value' => Q(rcube_label('save'))
		));
		$out .= $input->show();
		$this->rcmail->output->add_gui_object('save_account', '_save_acc');

		$out .= '</p>';
		$out .= '</div>';
		return $out;
	}

	function form_label($input_id, $label)
	{
		$label = Q($this->gettext($label));
		return sprintf('<label for="%s"><b>%s:</b></label>', $input_id, $label);
	}

	function forwardslist_html()
	{
		$forwards = $this->get_forwards();

		// Set up the columns to display.
		$cols = array(
			'vmail.source',
			'vmail.destination'
		);

		$out = rcube_table_output(array(
			'cols'        => 3,
			'cellpadding' => 0,
			'cellspacing' => 0,
			'class'       => 'records-table',
			'id'          => 'forwards-table'),
			$forwards, $cols, 'vmail.id');
		$this->rcmail->output->include_script('list.js');
		$this->rcmail->output->add_gui_object('forwardslist', 'forwards-table');
		return $out;
	}

	function forwardeditform_html()
	{
		$title = Q($this->gettext(($this->fid) ? 'editforward' : 'newforward'));
		$out = '<div id="account-title" class="boxtitle">' . $title . '</div>';
		$out .= '<div class="boxcontent">';
		$out .= $this->rcmail->output->form_tag(array(
			'id' => 'forwardeditform',
			'name' => 'forwardeditform',
			'method' => 'post',
			'action' => './?_task=settings&_action=plugin.forwards&_act=save'
		));
		$this->rcmail->output->add_gui_object('forward_form', 'forwardeditform');
		$hiddenfields = new html_hiddenfield(array(
			'name'  => '_fid',
			'value' => $this->fid
		));
		$out .= $hiddenfields->show();

		$table = new html_table(array('cols' => 2));

		$forward = ($this->forward) ? $this->forward : new Forward($this->fid);
		$source = get_user_part($forward->get('source'));

		// forward source input
		$input = new html_inputfield(array(
			'id'   => '_source',
			'name' => '_source',
			'size' => 50
		));
		$table->add('title', $this->form_label('_source', 'source'));
		$table->add(null, $input->show($source) . '@' . $this->domain_name);
		$this->rcmail->output->add_gui_object('source_input', '_source');

		// forward catchall checkbox
		$input = new html_checkbox(array(
			'id'    => '_catchall',
			'name'  => '_catchall',
			'value' => 1
		));
		$table->add('title', $this->form_label('_catchall', 'catchall'));
		$table->add(null, $input->show($forward->get('catchall')));
		$this->rcmail->output->add_gui_object('catchall_input', '_catchall');
		
		// forward destination input
		$input = new html_inputfield(array(
			'id'   => '_destination',
			'name' => '_destination',
			'size' => 50
		));
		$table->add('title', $this->form_label('_destination', 'destination'));
		$table->add(null, $input->show($forward->get('destination')));

		$out .= $table->show();
		$out .= '</form>';
		$out .= '<p>';

		// delete button
		$attr =  array(
			'id'    => '_delete_fwd',
			'class' => 'button',
			'name'  => '_action',
			'style' => 'margin-right: 0.5em',
			'type'  => 'button',
			'value' => Q(rcube_label('delete'))
		);
		if (!$this->fid) {
			$attr['disabled'] = true;
			$attr['style'] .= '; color: gray;';
		}
		$input = new html_inputfield($attr);
		$out .= $input->show();
		$this->rcmail->output->add_gui_object('del_forward', '_delete_fwd');

		// save button
		$input = new html_inputfield(array(
			'id'    => '_save_fwd',
			'class' => 'button mainaction',
			'name'  => '_action',
			'type'  => 'button',
			'value' => Q(rcube_label('save'))
		));
		$out .= $input->show();
		$this->rcmail->output->add_gui_object('save_forward', '_save_fwd');

		$out .= '</p>';
		$out .= '</div>';
		return $out;
	}
}
?>
