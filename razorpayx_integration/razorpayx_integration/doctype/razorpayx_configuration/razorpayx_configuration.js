// Copyright (c) 2024, Resilient Tech and contributors
// For license information, please see license.txt
const WEBHOOK_PATH = "razorpayx_integration.razorpayx_integration.utils.webhook.webhook_listener";

frappe.ui.form.on("RazorpayX Configuration", {
	setup: function (frm) {
		frm.set_query("bank_account", function () {
			return {
				filters: {
					is_company_account: 1,
					disabled: 0,
				},
			};
		});

		const coa_filters = {
			account_currency: "INR",
			freeze_account: "No",
		};

		frm.set_query("creditors_account", function () {
			return {
				filters: {
					...coa_filters,
					account_type: "Payable",
					root_type: "Liability",
				},
			};
		});

		frm.set_query("payable_account", function () {
			return {
				filters: {
					...coa_filters,
					account_type: "Liability",
				},
			};
		});
	},

	onload: function (frm) {
		if (!frm.is_new()) return;

		frm.set_intro(
			__(
				`Get RazorpayX API's Key <strong>ID</strong> and <strong>Secret</strong> from
					<a target="_blank" href="https://x.razorpay.com/settings/developer-controls">
						here {0}
					</a>
				if not available.`,
				[frappe.utils.icon("link-url")]
			)
		);
	},

	refresh: function (frm) {
		// listener to copy webhook url
		frm.$wrapper.find(".webhook-url").on("click", function () {
			frappe.utils.copy_to_clipboard(`${frappe.urllib.get_base_url()}/api/method/${WEBHOOK_PATH}`);
		});

		if (frm.doc.__islocal) return;

		frm.add_custom_button(__("Sync Transactions"), () => {
			prompt_transactions_sync_date(frm);
		});
	},

	after_save: function (frm) {
		if (frm.doc.webhook_secret) return;

		frappe.show_alert({
			message: __("Webhook Secret is missing! <br> You will not receive any updates!"),
			indicator: "orange",
		});
	},
});

function prompt_transactions_sync_date(frm) {
	const default_range = [frm.doc.last_sync_on || frappe.datetime.month_start(), frappe.datetime.now_date()];
	const dialog = new frappe.ui.Dialog({
		title: __("Sync {0} Transactions", [frm.doc.bank_account]),
		fields: [
			{
				label: __("Date Range"),
				fieldname: "date_range",
				fieldtype: "DateRange",
				reqd: 1,
				default: default_range,
			},
		],
		primary_action_label: __("{0} Sync", [frappe.utils.icon("refresh")]),
		primary_action: function (values) {
			sync_transactions(frm.docname, frm.doc.bank_account, ...values.date_range);
			dialog.hide();
		},
		size: "small",
	});

	dialog.get_field("date_range").datepicker.update({
		maxDate: new Date(frappe.datetime.get_today()),
	});

	// defaults are removed when setting maxDate
	dialog.set_df_property("date_range", "default", default_range);

	dialog.show();
}

function sync_transactions(razorpayx_config, bank_account, from_date, to_date) {
	frappe.show_alert({
		message: __("Syncing Transactions from <strong>{0}</strong> to <strong>{1}</strong>", [
			payment_integration_utils.get_date_in_user_fmt(from_date),
			payment_integration_utils.get_date_in_user_fmt(to_date),
		]),
		indicator: "blue",
	});

	frappe.call({
		method: "razorpayx_integration.razorpayx_integration.utils.bank_transaction.sync_bank_transactions_with_razorpayx",
		args: { razorpayx_config, bank_account, from_date, to_date },
		callback: function (r) {
			//TODO: If it is enqueued, need changes!!
			if (!r.exc) {
				frappe.show_alert({
					message: __("<strong>{0}</strong> transactions synced successfully!", [razorpayx_config]),
					indicator: "green",
				});
			}
		},
	});
}
