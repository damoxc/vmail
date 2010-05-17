<?php

/**
 * VMail plugin that allows for inserting a last login time 
 * using vlastlogin.
 *
 * @package plugins
 * @uses    rcube_plugin
 * @author  Damien Churchil <damien.churchill@ukplc.net>
 * @version 0.1
 * @license GPLv3
 * @link    https://www.uk-plc.net/os/rcube-vmail
 *
 */

class vmail_login extends rcube_plugin
{
	public $task = 'mail';

	function init()
	{
		$this->rcmail = &rcmail::get_instance();
		$this->add_hook('login_after',
			array($this, 'login_after_handler'));
	}

	function login_after_handler($args)
	{
		$username = $this->rcmail->user->data['username'];
		$remote_ip = $_SERVER['REMOTE_ADDR'];
		exec("vlastlogin '$username' 'rcube' '$remote_ip'");
		return $args;
	}
}
