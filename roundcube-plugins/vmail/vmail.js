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
			return rcmail.command('vmail-' + name);
		});
	
	return tab;
}

var vmail = {
	
	init: function() {
		// Create our tabs
		this.forwards_tab = create_tab('forwards', 'Forwards'),
			this.accounts_tab = create_tab('accounts', 'Accounts');
		rcmail.add_element(this.forwards_tab, 'tabs');
		rcmail.add_element(this.accounts_tab, 'tabs');

		// Configure the various commands
		rcmail.register_command('vmail-forwards', function() {
			rcmail.goto_url('plugin.forwards');
		}, true);
		rcmail.register_command('vmail-accounts', function() {
			rcmail.goto_url('plugin.accounts');
		}, true);

		rcmail.register_command('vmail-add', this.add_handler, true);
		rcmail.register_command('vmail-delete', this.delete_handler, true);
		rcmail.register_command('vmail-save', this.save_handler, true);

		// Exit early if this isn't forwards or accounts
		if (!rcmail.gui_objects.forwards_list && !rcmail.gui_objects.accounts_list)
			return;

		// Add the event handlers to the buttons next to destinations
		$('.dst-row').each(function() {
			$(this).find('.dst-delete-btn').click(vmail.delete_destination);;
			$(this).find('.dst-add-btn').click(vmail.add_destination);
		});

		// Initialize the forwards list if it exists
		if (rcmail.gui_objects.forwards_list) {
			this.init_forwards();
		} else if (rcmail.gui_objects.accounts_list) {
			this.init_accounts();
		}
	},

	init_accounts: function() {
		this.accounts_tab.addClass('tablink-selected');

		// This is valid when a new account is being created.
		if (rcmail.gui_objects.email_input) {
			rcmail.gui_objects.email_input.focus();
		}

		// Initialise the accounts list
		this.init_accounts_list();

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
			var setState = false;
			$('input[name=_forwarding]').each(function() {
				if ($(this).val() == 'std' && $(this).attr('checked')) {
					setState = true;
				}
			});
			vmail.set_forwarding_state(setState);

			// Add the event handler to change it on each click
			$('input[name=_forwarding]').click(function() {
				vmail.set_forwarding_state(($(this).val() == 'std'));
			});
		}

		if (rcmail.env.focus_field) {
			var field = $('#' + rcmail.env.focus_field);
			if (field) field.focus();
		}
	},

	init_forwards: function() {
		// Select our tab as the active one
		this.forwards_tab.addClass('tablink-selected');

		// Focus the source input if it exists
		if (!rcmail.env.fid && rcmail.gui_objects.source_input) {
			rcmail.gui_objects.source_input.focus();
		}

		// Configure the forwards list
		this.init_forwards_list();

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

		}
	},

	init_accounts_list: function() {
		vmail.accounts_list = new rcube_list_widget(rcmail.gui_objects.accounts_list, {
			multiselect: false,
			draggable:   false,
			keyboard:    false
		});

		// Handle loading the accounts when they are selected in the list
		vmail.accounts_list.addEventListener('select', function(list) {
			var id = list.get_single_selection();

			// If there's no selection for whatever reason, return
			if (id == null)
				return;

			// Change the quota image on the old selection if there is one
			if (vmail.selected_account) {
				vmail.switch_quota_image(vmail.selected_account);
			}

			// Change the quota image on the new selection
			vmail.switch_quota_image(id);
			vmail.selected_account = id;

			vmail.load_account(id, 'edit');
		});
		vmail.accounts_list.init();
		vmail.accounts_list.focus();

		if (rcmail.env.aid) {
			vmail.accounts_list.select(rcmail.env.aid);
		}
	},

	init_forwards_list: function() {
		vmail.forwards_list = new rcube_list_widget(rcmail.gui_objects.forwards_list, {
			multiselect: false,
			draggable:   false,
			keyboard:    false
		});

		vmail.forwards_list.addEventListener('select', function(list) {
			var id = list.get_single_selection();
			if (id == null) return;
			vmail.load_forward(id, 'edit');
		});

		vmail.forwards_list.init();
		vmail.forwards_list.focus();
		if (rcmail.env.fid && rcmail.env.act != 'del') {
			vmail.forwards_list.select(rcmail.env.fid);
			$('#forwards-list')[0].scrollTop = vmail.forwards_list.rows[rcmail.env.fid].obj.offsetTop;
		}
	},

	load_account: function(id, action) {
		if (action == 'edit' && (!id || id == rcmail.env.aid))
			return false;

		if (action && (id || action == 'add'))
			rcmail.goto_url('plugin.edit-account', '_aid='+id+'&_token='+rcmail.env.request_token, true);
	},

	load_forward: function(id, action) {
		if (action == 'edit' && (!id || id == rcmail.env.fid))
			return false;

		if (action && (id || action == 'add')) {
			rcmail.goto_url('plugin.edit-forward', '_fid='+id+'&_token='+rcmail.env.request_token, true);
		}
	},

	add_handler: function(command) {
		rcmail.goto_url('plugin.add-' + command);
	},

	delete_handler: function(command) {
		var selection = vmail[command + 's_list'].get_selection();
		var id_name = (command == 'forward') ? 'fid' : 'aid';
		var env_id = rcmail.env[id_name];

		if (!(selection.length || env_id))
			return;

		var id = env_id ? env_id : selection[0];

		if (!confirm('Are you sure you wish to delete this ' + command + '?'))
			return;

		rcmail.goto_url('plugin.delete-' + command, '_' + id_name + '='+id+'&_token='+rcmail.env.request_token, true);
	},

	save_handler: function(command) {
		rcmail.gui_objects[command + '_form'].submit();
	},

	/**
	 * Handle removing a destination input from the form.
	 */
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
	
	/**
	 * Add a new destination input to the form, below the input that had
	 * its add button clicked.
	 */
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
		newRow.find('.dst-delete-btn').click(vmail.delete_destination);;
		newRow.find('.dst-add-btn').click(vmail.add_destination);
		currentRow.after(newRow);
	},

	set_forwarding_state: function(enabled) {
		if (enabled) {
			$('input[name=_savecopy]').attr('disabled', true).addClass('disabled');
			$('.dst-row input')
				.attr('disabled', true)
				.addClass('disabled');
			$('.dst-help')
				.addClass('disabled');
		} else {
			$('input[name=_savecopy]').attr('disabled', false).removeClass('disabled');
			$('.dst-row input')
				.attr('disabled', false)
				.removeClass('disabled');
			$('.dst-help')
				.removeClass('disabled');

			// Disable the delete button if needs be afterwards
			if ($('.dst-row').length == 1) {
				$('.dst-row .dst-delete-btn')
					.attr('disabled', true)
					.addClass('disabled');
			}
				
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
	}
}

if (window.rcmail) {
	rcmail.addEventListener('init', function(env) {
		vmail.init.call(vmail);
	});
}
