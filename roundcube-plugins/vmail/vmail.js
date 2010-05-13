/* Show user_settings plugin script */

function create_tab(name, label) {
	var tab = $('<span>').attr('id', 'settingstabplugin' + name).addClass('tablink');
	var button = $('<a>').attr('href', rcmail.env.comm_path + '&_action=plugin.' + name)
		.html(rcmail.gettext(label, 'vmail'))
		.appendTo(tab);
	return {'tab': tab, 'button': button};
}

var forwards = {
	
	init: function() {
		var elms = create_tab('forwards', 'Forwards');
		this.tab = elms.tab;
		this.button = elms.button;
		this.button.bind('click', function(e) {
			return rcmail.command('plugin.forwards', this);
		});

		rcmail.add_element(this.tab, 'tabs');
		rcmail.register_command('plugin.forwards', function() {
			rcmail.goto_url('plugin.forwards');
		}, true);
		rcmail.register_command('plugin.forward-new', function() {
			forwards.goto_url('new');
		}, true);

		rcmail.env.forwards_path = rcmail.env.comm_path + '&_action=plugin.forwards';

		if (rcmail.gui_objects.forwardslist) {
			this.init_forwardslist();
		}

		if (!rcmail.env.fid && rcmail.gui_objects.source_input) {
			rcmail.gui_objects.source_input.focus();
		}

		// These are valid for edit/creating forwards.
		if (rcmail.gui_objects.forward_form) {
			$(rcmail.gui_objects.del_forward).click(function() {
				if (!confirm('Are you sure you wish to delete this forward?')) return;
				forwards.goto_url('del', rcmail.env.fid);
			});

			$(rcmail.gui_objects.save_forward).click(function() {
				rcmail.gui_objects.forward_form.submit();
			});

			if (rcmail.gui_objects.catchall_input.checked) {
				rcmail.gui_objects.source_input.disabled = true;
				$(rcmail.gui_objects.source_input.parentNode).addClass('disabled');
			}

			$(rcmail.gui_objects.catchall_input).click(function() {
				if (rcmail.gui_objects.catchall_input.checked) {
					rcmail.gui_objects.source_input.disabled = true;
					$(rcmail.gui_objects.source_input.parentNode).addClass('disabled');
				} else {
					rcmail.gui_objects.source_input.disabled = false;
					$(rcmail.gui_objects.source_input.parentNode).removeClass('disabled');
					rcmail.gui_objects.source_input.focus();
				}
			});
		}
	},

	init_forwardslist: function() {
		rcmail.forwardslist = new rcube_list_widget(rcmail.gui_objects.forwardslist, {
			multiselect: false,
			draggable:   false,
			keyboard:    false
		});
		rcmail.forwardslist.addEventListener('select', this.on_forward_select);
		rcmail.forwardslist.init();
		rcmail.forwardslist.focus();
		if (rcmail.env.fid && rcmail.env.act != 'del') {
			rcmail.forwardslist.select(rcmail.env.fid);
			$('#forwards-list')[0].scrollTop = rcmail.forwardslist.rows[rcmail.env.fid].obj.offsetTop;
		}
	},

	on_forward_select: function(list) {
		var id = list.get_single_selection();
		if (id == null) return;
		forwards.load_forward(id, 'edit');
	},

	goto_url: function(action, fid) {
		var add_url = '&_act=' + action;
		var target = window;
		if (rcmail.env.contentframe && window.frames && window.frames[rcmail.env.contentframe]) {
			add_url += '&_framed=1';
			target = window.frames[rcmail.env.contentframe];
			document.getElementById(rcmail.env.contentframe).style.visibility = 'inherit';
		}
		if (fid > 0) add_url += '&_fid=' + fid;

		rcmail.set_busy(true);
		target.location.href = rcmail.env.forwards_path + add_url;
	},

	load_forward: function(id, action) {
		if (action == 'edit' && (!id || id == rcmail.env.fid))
			return false;

		if (action && (id || action == 'add')) this.goto_url(action, id);
	}
}

var accounts = {
	
	init: function() {
		var elms = create_tab('accounts', 'Accounts');
		this.tab = elms.tab;
		this.button = elms.button;
		this.button.bind('click', function(e) {
			return rcmail.command('plugin.accounts', this)
		});


		// add button and register command
		rcmail.add_element(this.tab, 'tabs');
		rcmail.register_command('plugin.accounts', function() {
			rcmail.goto_url('plugin.accounts');
		}, true);
		rcmail.register_command('plugin.account-new', function() {
			accounts.goto_url('new');
		}, true);

		rcmail.env.accounts_path = rcmail.env.comm_path + '&_action=plugin.accounts';

		if (rcmail.gui_objects.accountslist) {
			this.init_accountslist();
		}

		// This is valid when a new account is being created.
		if (rcmail.gui_objects.email_input) {
			rcmail.gui_objects.email_input.focus();
		}

		// These are valid for edit/creating accounts.
		if (rcmail.gui_objects.account_form) {
			$(rcmail.gui_objects.del_account).click(function() {
				if (!confirm('Are you sure you wish to delete this account?')) return;
				accounts.goto_url('del', rcmail.env.aid);
			});
			$(rcmail.gui_objects.save_account).click(function() {
				rcmail.gui_objects.account_form.submit();
			});

			var sel = $(rcmail.gui_objects.quota_input);
			var after = sel.parent().parent();
			var row = $(rcmail.gui_objects.quotaother_input).parent().parent();
			if (sel.val() != 'other') row.remove();
			function on_sel_change() {
				if (sel.val() == 'other') {
					row.insertAfter(after);
					$(rcmail.gui_objects.quotaother_input).focus();
				} else {
					row.remove();
				}
			}
			sel.change(on_sel_change);
			sel.blur(on_sel_change);
		}

		if (rcmail.env.focus_field) {
			var field = $('#' + rcmail.env.focus_field);
			if (field) field.focus();
		}
	},

	init_accountslist: function() {
		rcmail.accountslist = new rcube_list_widget(rcmail.gui_objects.accountslist, {
			multiselect: false,
			draggable:   false,
			keyboard:    false
		});
		rcmail.accountslist.addEventListener('select', this.on_account_select);
		rcmail.accountslist.init();
		rcmail.accountslist.focus();

		for (var i = 1; i < rcmail.accountslist.rowcount; i++) {
			var row = rcmail.accountslist.rows[i];
			if (!row) continue;
			if ($(row.obj.firstChild).text() == rcmail.env.user) {
				$(row.obj).addClass('current-user');
			}
		}

		if (rcmail.env.aid) {
			rcmail.accountslist.select(rcmail.env.aid);
		}
	},

	goto_url: function(action, aid) {
		var add_url = '&_act=' + action;
		var target = window;
		if (rcmail.env.contentframe && window.frames && window.frames[rcmail.env.contentframe]) {
			add_url += '&_framed=1';
			target = window.frames[rcmail.env.contentframe];
			document.getElementById(rcmail.env.contentframe).style.visibility = 'inherit';
		}
		if (aid > 0) add_url += '&_aid=' + aid;

		rcmail.set_busy(true);
		target.location.href = rcmail.env.accounts_path + add_url;
	},

	post_url: function(action, aid, data) {
		rcmail.set_busy(true);
	},

	on_account_select: function(list) {
		var id = list.get_single_selection();
		if (id == null) return;
		accounts.load_account(id, 'edit');
	},

	load_account: function(id, action) {
		if (action == 'edit' && (!id || id == rcmail.env.aid))
			return false;

		if (action && (id || action == 'add')) this.goto_url(action, id);
	}
};

if (window.rcmail) {
	rcmail.addEventListener('init', function(env) {
		forwards.init.call(forwards);
		accounts.init.call(accounts);
	});
}
