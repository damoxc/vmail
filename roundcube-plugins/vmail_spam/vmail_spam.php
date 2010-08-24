<?php

/**
 * VMail Spam
 *
 * Plugin that adds vmails spam training facilities to Roundcube.
 *
 * @version 0.1
 * @author Damien Churchill <damoxc@gmail.com>
 */

class vmail_spam extends rcube_plugin {

	public $task = 'mail';

	function init()
	{
		$this->register_action('plugin.vmail_spam', array($this, 'handle_request'));

		$rcmail = rcmail::get_instance();

		if ($rcmail->action == '' || $rcmail->action == 'show') {
			$skin_path = $this->local_skin_path();
			$this->include_script('vmail_spam.js');
			$this->add_texts('localization', true);

			if (get_input_value('_mbox', RCUBE_INPUT_GET) == 'Junk') {
				$this->add_button(array(
					'id'       => 'vmail_spambtn',
					'alt'      => $this->gettext('vmail_spam.markjunk'),
					'command'  => 'plugin.vmail_spam',
					'imagepas' => $skin_path.'/notjunk_pas.png',
					'imageact' => $skin_path.'/notjunk_act.png',
					'title'    => 'vmail_spam.marknotjunk'), 'toolbar');
			} else {
				$this->add_button(array(
					'id'       => 'vmail_spambtn',
					'alt'      => $this->gettext('vmail_spam.marknotjunk'),
					'command'  => 'plugin.vmail_spam',
					'imagepas' => $skin_path.'/junk_pas.png',
					'imageact' => $skin_path.'/junk_act.png',
					'title'    => 'vmail_spam.markjunk'), 'toolbar');
			}
		}
	}

	function handle_request()
	{
		$this->add_texts('localization', true);

		$GLOBALS['IMAP_FLAGS']['JUNK'] = 'Junk';
		$GLOBALS['IMAP_FLAGS']['NONJUNK'] = 'NonJunk';

		$uids = get_input_value('_uid', RCUBE_INPUT_POST);
		$mbox = get_input_value('_mbox', RCUBE_INPUT_POST);

		$rcmail = rcmail::get_instance();
		$junk_mbox = $rcmail->config->get('junk_mbox');

		$_uids = explode(',', $uids);

		if ($mbox == $junk_mbox) {
			$rcmail->imap->unset_flag($uids, 'JUNK');
			$rcmail->imap->set_flag($uids, 'NONJUNK');

			$rcmail->output->command('move_messages', "INBOX");
			$rcmail->output->command('display_message', $this->gettext('reportedasnotjunk'), 'confirmation');
		} else {
			$rcmail->imap->unset_flag($uids, 'NONJUNK');
			$rcmail->imap->set_flag($uids, 'JUNK');

			$rcmail->output->command('move_messages', $junk_mbox);
			$rcmail->output->command('display_message', $this->gettext('reportedasjunk'), 'confirmation');
		}
		$rcmail->output->send();
	}
}
