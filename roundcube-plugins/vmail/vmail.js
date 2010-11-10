/* Vmail plugin script */
function create_tab(name, label) {
	var tab = $('<span>')
		.attr('id', 'settingstabplugin' + name)
		.addClass('tablink');

	var button = $('<a>')
		.attr('href', rcmail.env.comm_path + '&_action=plugin.' + name)
		.html(rcmail.gettext(label, 'vmail'))
		.appendTo(tab)
		.click(function() {
			return rcmail.command('plugin.' + name);
		});
	
	return tab;
}

var forwards = {
	
	init: function() {
		// Create our tab
		this.tab = create_tab('forwards', 'Forwards');
		rcmail.add_element(this.tab, 'tabs');

		// Configure the various commands
		rcmail.register_command('plugin.forwards', function() {
			rcmail.goto_url('plugin.forwards');
		}, true);
		rcmail.register_command('add-forward', function() {
			rcmail.goto_url('plugin.add-forward');
		}, true);
		rcmail.register_command('delete-forward', this.delete_forward, true);
		rcmail.register_command('save-forward', function() {
			rcmail.gui_objects.forward_form.submit();
		}, true);

		// Initialize the forwards list if it exists
		if (rcmail.gui_objects.forwards_list) {
			this.init_forwards_list();
			this.tab.addClass('tablink-selected');
		}

		// Focus the source input if it exists
		if (!rcmail.env.fid && rcmail.gui_objects.source_input) {
			rcmail.gui_objects.source_input.focus();
		}

		// These are valid for edit/creating forwards.
		if (rcmail.gui_objects.forward_form) {
			// Disable the source input if catchall is enabled
			if (rcmail.gui_objects.catchall_input.checked) {
				$(rcmail.gui_objects.source_input)
					.attr('disabled', true)
					.parent().addClass('disabled');
			}

			// Add the event handler to listen for this and act accordinly
			$(rcmail.gui_objects.catchall_input).click(function() {
				if (rcmail.gui_objects.catchall_input.checked) {
					$(rcmail.gui_objects.source_input)
						.attr('disabled', true)
						.parent().addClass('disabled');
				} else {
					$(rcmail.gui_objects.source_input)
						.attr('disabled', false)
						.parent().removeClass('disabled');
				}
			});

			// Add the event handlers to the buttons next to destinations
			$('.dst-row').each(function() {
				$(this).find('.dst-delete-btn').click(forwards.delete_destination);;
				$(this).find('.dst-add-btn').click(forwards.add_destination);
			});
		}
	},

	init_forwards_list: function() {
		rcmail.forwards_list = new rcube_list_widget(rcmail.gui_objects.forwards_list, {
			multiselect: false,
			draggable:   false,
			keyboard:    false
		});
		rcmail.forwards_list.addEventListener('select', this.on_forward_select);
		rcmail.forwards_list.init();
		rcmail.forwards_list.focus();
		if (rcmail.env.fid && rcmail.env.act != 'del') {
			rcmail.forwards_list.select(rcmail.env.fid);
			$('#forwards-list')[0].scrollTop = rcmail.forwards_list.rows[rcmail.env.fid].obj.offsetTop;
		}
	},

	on_forward_select: function(list) {
		var id = list.get_single_selection();
		if (id == null) return;
		forwards.load_forward(id, 'edit');
	},

	load_forward: function(id, action) {
		if (action == 'edit' && (!id || id == rcmail.env.fid))
			return false;

		if (action && (id || action == 'add')) {
			rcmail.goto_url('plugin.edit-forward', '_fid='+id+'&_token='+rcmail.env.request_token, true);
		}
	},

	delete_forward: function(id) {
		var selection = rcmail.forwards_list.get_selection();
		if (!(selection.length || rcmail.env.fid))
			return;

		if (!confirm('Are you sure you wish to delete this forward?'))
			return;

		if (!id)
			id = rcmail.env.fid ? rcmail.env.fid : selection[0];

		rcmail.goto_url('plugin.delete-forward', '_fid='+id+'&_token='+rcmail.env.request_token, true);

		return true;
	},

	delete_destination: function() {
		$(this).parent().parent().remove();
		
		// We want to disable the delete button for this row as there 
		// must always be one destination.
		if ($('.dst-row').length == 1) {
			$('.dst-row').find('.dst-delete-btn')
				.attr('disabled', true)
				.addClass('disabled');
		}
	},

	add_destination: function() {
		var currentRow = $(this).parent().parent();

		// Here we need to enable the disabled delete button for the single
		// row as there are now 2, making it a valid target for deletion.
		if ($('.dst-row').length == 1) {
			currentRow.find('.dst-delete-btn')
				.attr('disabled', false)
				.removeClass('disabled');
		}

		// Lastly add the new row to the table
		var newRow = currentRow.clone();
		newRow.find('.dst-input').val('');
		newRow.find('.dst-delete-btn').click(forwards.delete_destination);;
		newRow.find('.dst-add-btn').click(forwards.add_destination);
		currentRow.after(newRow);
	}
}

var accounts = {
	
	init: function() {
		// Add our tab to the page
		this.tab = create_tab('accounts', 'Accounts');
		rcmail.add_element(this.tab, 'tabs');

		// add button and register command
		rcmail.register_command('plugin.accounts', function() {
			rcmail.goto_url('plugin.accounts');
		}, true);
		rcmail.register_command('add-account', function() {
			rcmail.goto_url('plugin.add-account');
		}, true);
		rcmail.register_command('delete-account', accounts.delete_account, true);
		rcmail.register_command('save-account', function() {
			rcmail.gui_objects.account_form.submit();
		}, true);

		rcmail.env.accounts_path = rcmail.env.comm_path + '&_action=plugin.accounts';

		if (rcmail.gui_objects.accountslist) {
			this.init_accountslist();
			this.tab.addClass('tablink-selected');
		}

		// This is valid when a new account is being created.
		if (rcmail.gui_objects.email_input) {
			rcmail.gui_objects.email_input.focus();
		}

		// These are valid for edit/creating accounts.
		if (rcmail.gui_objects.account_form) {
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

			// Set the forwarding disabled state
			accounts.set_forwarding_state($('input[name=_forwarding][checked=checked]').val() == 'std');
			$('input[name=_forwarding]').click(function() {
				accounts.set_forwarding_state(($(this).val() == 'std'));
			});
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

		if (rcmail.env.aid) {
			rcmail.accountslist.select(rcmail.env.aid);
		}
	},

	set_forwarding_state: function(enabled) {
		if (enabled) {
			$('input[name=_forwardto],input[name=_savecopy]').attr('disabled', true).addClass('disabled');
		} else {
			$('#_forwardto').attr('disabled', false).removeClass('disabled');
			$('input[name=_savecopy]').attr('disabled', false).removeClass('disabled');
		}
	},

	switch_quota_image: function(id) {
		var src = $('#rcmrow' + id + ' .user_quota img').attr('src');
		if (src.indexOf('quota_sel') >= 0) {
			src = src.split('/').slice(0, -1);
			src.push('quota.gif');
			src = src.join('/');
		} else {
			src = src.split('/').slice(0, -1);
			src.push('quota_sel.gif');
			src = src.join('/');
		}
		$('#rcmrow' + id + ' .user_quota img').attr('src', src);
	},

	on_account_select: function(list) {
		var id = list.get_single_selection();

		// If there's no selection for whatever reason, return
		if (id == null)
			return;

		// Change the quota image on the old selection if there is one
		if (accounts.selected) {
			accounts.switch_quota_image(accounts.selected);
		}

		// Change the quota image on the new selection
		accounts.switch_quota_image(id);
		accounts.selected = id;

		accounts.load_account(id, 'edit');
	},

	delete_account: function(id) {
		var selection = rcmail.accountslist.get_selection();
		if (!(selection.length || rcmail.env.aid))
			return;

		if (!confirm('Are you sure you wish to delete this account?'))
			return;

		if (!id)
			id = rcmail.env.aid ? rcmail.env.aid : selection[0];

		rcmail.goto_url('plugin.delete-account', '_aid='+id+'&_token='+rcmail.env.request_token, true);

		return true;
	},

	load_account: function(id, action) {
		if (action == 'edit' && (!id || id == rcmail.env.aid))
			return false;

		if (action && (id || action == 'add'))
			rcmail.goto_url('plugin.edit-account', '_aid='+id+'&_token='+rcmail.env.request_token, true);
	}
};

if (window.rcmail) {
	rcmail.addEventListener('init', function(env) {
		forwards.init.call(forwards);
		accounts.init.call(accounts);
	});
}
