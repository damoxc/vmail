if (window.rcmail) {
	rcmail.addEventListener('init', function(env) {
		if (!rcmail.env.action.match('^plugin.') && rcmail.gui_objects.newpasswd_input) {
			var input = $(rcmail.gui_objects.newpasswd_input);
			input.parent().after('<td rowspan=2 style="vertical-align: top;">'
				+ '<div id="password-info" style="width: 200px">'
					+ '<a href="#" tabindex=999>Password strength:</a>'
				 	+ '<span id="pwd-strength-txt" style="float: right; font-weight: bold;"></span>'
				 	+ '<div id="pwd-strength-bkg" style="height: 4px; background: #ccc; margin-top: 2px; position: relative;">'
				 		+ '<div id="pwd-strength-bar" style="height: 4px;"></div>'
					+ '</div>'
				+ '</div>'
			+ '</td>');

			var strength = $('#pwd-strength-txt'), bar = $('#pwd-strength-bar');
			var sChars = '[\?!\.\$%\^\*]';

			input.keyup(function(e) {
				var pwd = input.val();
				if (pwd.length == 0) {
					strength.text('');
					bar.css('width', '0%');
				} else if (pwd.length < 8) {
					strength.css('color', 'black');
					strength.text('Too short');
					bar.css('width', '0%');
				} else if (pwd.match('[a-zA-Z]') && pwd.match('[0-9]') && pwd.match(sChars) && pwd.length >= 16) {
					strength.css('color', 'green');
					strength.text('Strong');
					bar.css('width', '100%');
					bar.css('background', 'green');
				} else if (pwd.match('[a-zA-Z]') && pwd.match('[0-9]') && (pwd.match(sChars) || pwd.length >= 16)) {
					strength.css('color', 'green');
					strength.text('Good');
					bar.css('width', '75%');
					bar.css('background', 'green');
				} else if (pwd.match('[a-zA-Z]') && pwd.match('[0-9]')) {
					strength.css('color', 'orange');
					strength.text('Medium');
					bar.css('width', '50%');
					bar.css('background', 'orange');
				} else if (pwd.match('^[a-zA-Z]+$')) {
					strength.css('color', 'red');
					strength.text('Weak');
					bar.css('width', '25%');
					bar.css('background', 'red');
				}
			});
		}
	});
}
