/* Vmail Spam plugin script */
function vmail_spam(prop)
{
	if (!rcmail.env.uid && (!rcmail.message_list || !rcmail.message_list.get_selection().length))
		return;
  
	var uids = rcmail.env.uid ? rcmail.env.uid : rcmail.message_list.get_selection().join(',');
    
	rcmail.set_busy(true, 'loading');
	rcmail.http_post('plugin.vmail_spam', '_uid='+uids+'&_mbox='+urlencode(rcmail.env.mailbox), true);
}

function update_button(folder, force) {
	var btn = rcmail.buttons['plugin.vmail_spam'][0];
	var mode = (folder != 'Junk') ? 'junk' : 'notjunk';
	if (mode == btn.mode && !force) return;


	if (mode == 'junk') {
		btn.act = btn.base_path + '/junk_act.png';
		btn.pas = btn.base_path + '/junk_pas.png';
		btn.image.title = btn.junk_title;
	} else {
		btn.act = btn.base_path + '/notjunk_act.png';
		btn.pas = btn.base_path + '/notjunk_pas.png';
		btn.image.title = btn.notjunk_title;
	}
	btn.mode = mode;
	btn.image.src = btn.pas;
}

// callback for app-onload event
if (window.rcmail) {
	rcmail.addEventListener('init', function(evt) {
    
		// register command (directly enable in message view mode)
		rcmail.register_command('plugin.vmail_spam', vmail_spam, rcmail.env.uid);


		// add event-listener to message list
		if (rcmail.message_list) {
			var btn = rcmail.buttons['plugin.vmail_spam'][0];
			btn.mode = (rcmail.env.mailbox != 'Junk') ? 'junk' : 'notjunk';
			btn.base_path = btn.act.split('/').slice(0, -1).join('/');
			btn.image = $('#vmail_spambtn')[0];
			if (btn.mode == 'junk') {
				btn.junk_title = btn.image.title;
				btn.notjunk_title = btn.image.alt.substring(1, btn.image.alt.length - 1);
			} else {
				btn.notjunk_title = btn.image.title;
				btn.junk_title = btn.image.alt.substring(1, btn.image.alt.length - 1);
			}
			update_button(rcmail.env.mailbox, true);

			rcmail.message_list.addEventListener('select', function(list){
				rcmail.enable_command('plugin.vmail_spam', list.get_selection().length > 0);
			});
			rcmail.addEventListener('selectfolder', function(e) {
				update_button(e.folder);
			});
		}
	});
}

