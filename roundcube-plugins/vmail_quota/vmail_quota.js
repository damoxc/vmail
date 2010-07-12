/*!
 * Adds the domain quota to the mailbox view
 */

if (window.rcmail) {
	rcmail.addEventListener('init', function(env) {
		var elm = $('#listcontrols');
		if (!elm.length) return;

		$('#quotadisplay').prev().text('Account usage:');
		elm.append($.create('span', {
			style: 'margin-left: 120px; margin-right: 5px'
		}, ['Domain usage:']));

		elm.append($.create('span', {
			id: 'domainquota',
			style: 'position: relative;'
		}));

		var q = rcmail.env.dom_quota;
		if (q.error) {
			var cls = 'quota_low',
			    txtcls = 'quota_text_normal',
				title = 'unknown'
				text = ['unknown'];
		} else if (q.usage >= 80) {
			var cls = 'quota_high',
			    txtcls = 'quota_text_high',
				title = q.used + ' / ' + q.total + ' (' + q.usage + '%)',
				text = [q.usage + '%'];
		} else if (q.usage >= 55) {
			var cls = 'quota_mid',
			    txtcls = 'quota_text_mid',
				title = q.used + ' / ' + q.total + ' (' + q.usage + '%)',
				text = [q.usage + '%'];
		} else {
			var cls = 'quota_low',
			    txtcls = 'quota_text_normal',
				title = q.used + ' / ' + q.total + ' (' + q.usage + '%)',
				text = [q.usage + '%'];
		}
		elm = $('#domainquota');
		elm.append($.create('div', {
			style: 'position: absolute; top: 1px; left: 1px; width: ' + q.usage + 'px; height: 14px; z-index:99;',
			'class': cls
		}));
		elm.append($.create('div', {
			style: 'position: absolute; top: 1px; left: 1px; width: 100px; height: 14px; z-index:98;',
			'class': 'quota_bg'
		}));
		elm.append($.create('div', {
			style: 'position: absolute; top: 0px; left: 0px; width: 100px; height: 14px; z-index:100;',
			'class': 'quota_text ' + txtcls,
			title: title
		}, text));
	});
}
