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
	private $request_id = 0;

	function __construct()
	{
		$this->sock_path = getconfig('socket');
		$this->sock = socket_create(AF_UNIX, SOCK_STREAM, 0);
		socket_connect($this->sock, $this->sock_path);
	}

	function __destruct()
	{
		socket_close($this->sock);
	}

	function __get($name = null)
	{
		return new DottedObject($name, $this);
	}

	function _call($method, $arguments)
	{
		$request = json_encode(array(
			id     => $this->request_id,
			method => $method,
			args   => $arguments
		));
		$this->request_id++;
		socket_write($this->sock, $request);
		$response = json_decode(socket_read($this->sock, 4096));

		if ($response->error) {
			raise_error(array(
				code    => 1,
				type    => 'vmail',
				message => '(' . $response->error->name . ') ' . $response->error->value
			), true);
		} else {
			return $response->result;
		}
	}
}
?>
