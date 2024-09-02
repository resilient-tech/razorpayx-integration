// Copyright (c) 2024, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("RazorPayX Integration Setting", {
	setup: function (frm) {
		frm.set_query("bank_account", function () {
			return {
				filters: { is_company_account: 1 },
			};
		});
	},

	onload: function (frm) {
		if (frm.is_new()) {
			frm.set_intro(
				__(
					`Get RazorPayX API's Key <strong>Id</strong> and <strong>Secret</strong> from
						<a target="_blank" href="https://x.razorpay.com/settings/developer-controls">
							here {0}
						</a>
					if not available.`,
					[frappe.utils.icon("link-url")]
				)
			);
		}
	},

	refresh: function (frm) {
		if (frm.is_new() || frm.doc.status === "disabled") return;

		frm.add_custom_button(__("{0} Sync Bank Transactions", [frappe.utils.icon("refresh")]), () =>
			prompt_for_transactions_sync_date(frm)
		);
	},
});

function prompt_for_transactions_sync_date(frm) {
	frappe.prompt(
		[
			{
				label: "From Date",
				fieldname: "from_date",
				fieldtype: "Date",
				reqd: 1,
				max_date: new Date(frappe.datetime.get_today()),
			},
		],
		(values) => sync_bank_transactions(frm, values.from_date),
		"Sync Bank Transactions",
		"Sync"
	);
}

async function sync_bank_transactions(frm, from_date) {
	const params = {
		method: "razorpayx_integration.razorpayx_integration.utils.transaction.sync_bank_transactions",
		args: {
			bank_account: frm.doc.bank_account,
			from_date: from_date,
		},
		freeze: true,
		freeze_message: __("Synchronizing Bank Transaction From {0}", [
			razorpayx_integration.get_date_in_user_fmt(from_date),
		]),
	};

	const response = await frappe.call(params);

	if (!response.message) {
		frappe.show_alert({ message: __("Synchronization failed. Please try again."), indicator: "red" });
	} else {
		frappe.show_alert({ message: __("Synchronization completed successfully."), indicator: "green" });
	}
}
