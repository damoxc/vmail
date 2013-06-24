<?php
require_once 'funcs.inc';

class DottedObject
{
	private $name = '';
	private $client = null;

	function __construct($name, $client)
	{
		$this->name = $name;
		$this->client = $client;
	}

	function __call($name, $arguments)
	{
		$name = "$this->name.$name";
		return $this->client->_call($name, $arguments);
	}
}

class VClient
{
	private $sock_path;
	private $sock;
	private $connected = false;
	private $request_id = 0;

	function __construct()
	{
		$this->sock_path = getconfig('socket');

		if (strlen($this->sock_path) == 0) {
			return raise_error(array(
				code    => 1,
				type    => 'vmail',
				message => "Invalid socket path"
			), true);
		}


		$this->sock = socket_create(AF_UNIX, SOCK_STREAM, 0);

		// Check for any errors when trying to connect to the socket
		if ($this->sock === false) {
			$errorcode = socket_last_error();
			$errormsg = socket_strerror($errorcode);

			return raise_error(array(
				code    => $errorcode,
				type    => 'vmail',
				message => "Could not connect to socket: $errormsg"
			), true);
		}

		if (socket_connect($this->sock, $this->sock_path) === false) {
			$errorcode = socket_last_error();
			$errormsg = socket_strerror($errorcode);

			return raise_error(array(
				code    => $errorcode,
				type    => 'vmail',
				message => "Could not connect to socket: $errormsg"
			), true);
		}

		$this->connected = true;
	}

	function __destruct()
	{
		if ($this->connected === false) return;
		socket_close($this->sock);
	}

	function __get($name = null)
	{
		return new DottedObject($name, $this);
	}

	function _call($method, $arguments)
	{
		if ($this->connected === false) {
			raise_error(array(
				code    => 2,
				type    => 'vmail',
				message => "Not connected to socket"
			), true);
			return;
		}

		$request = json_encode(array(
			'id'     => $this->request_id,
			'method' => $method,
			'params' => $arguments
		)) . "\n";
		$this->request_id++;

		if (socket_write($this->sock, $request) === false) {
			$errorcode = socket_last_error();
			$errormsg = socket_strerror($errorcode);

			return raise_error(array(
				code    => $errorcode,
				type    => 'vmail',
				message => "Could not write to socket: $errormsg"
			), true);
		}

		// Read the initial data from the socket
		$buffer = socket_read($this->sock, 4096);

		// Check for any errors when trying to read from the socket
		if ($buffer === false) {
			$errorcode = socket_last_error();
			$errormsg = socket_strerror($errorcode);

			return raise_error(array(
				code    => $errorcode,
				type    => 'vmail',
				message => "Could not read from socket: $errormsg"
			), true);
		}

		// Try to decode the data and read any further data if required
		while (($response = json_decode($buffer)) == NULL) {
			$data = socket_read($this->sock, 4096);

			// Check for any errors when trying to read from the socket
			if ($data === false) {
				$errorcode = socket_last_error();
				$errormsg = socket_strerror($errorcode);

				return raise_error(array(
					code    => $errorcode,
					type    => 'vmail',
					message => "Could not read from socket: $errormsg"
				), true);
			}

			$buffer .= $data;
		}

		// Check to see if we have an error response
		if ($response->error) {
			raise_error(array(
				code    => 15,
				type    => 'vmail',
				message => '(' . $response->error->name . ') ' . $response->error->value
			), true);
			return NULL;
		} else {
			return $response->result;
		}
	}
}
?>
