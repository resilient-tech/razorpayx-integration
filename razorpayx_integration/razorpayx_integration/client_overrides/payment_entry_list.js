// Copyright (c) 2025, Resilient Tech and contributors
// For license information, please see license.txt

frappe.listview_settings["Payment Entry"] = {
	add_fields: ["make_bank_online_payment", "razorpayx_account", "razorpayx_payout_status"],

	onload: function (list_view) {
		// Remove the Submit button from the Payment Entry list view
		list_view.page.actions
			.find(`[data-label="${encodeURIComponent(__("Submit"))}"]`)
			.closest("li")
			.remove();

		// Add `Pay and Submit` button to the Payment Entry list view
		if (!rpx.user_has_payout_permissions()) return;

		list_view.page.add_actions_menu_item(__("Pay and Submit"), () => {
			const selected_docs = list_view.get_checked_items();
			const eligible_docs = [];
			const ineligible_docs = [];

			selected_docs.forEach((doc) => {
				if (is_eligible(doc)) {
					eligible_docs.push(doc.name);
				} else {
					ineligible_docs.push(doc.name);
				}
			});

			if (!eligible_docs.length) {
				frappe.msgprint(
					__("Please select proper Payment Entries to pay and submit."),
					__("Invalid Selection")
				);
				return;
			}

			if (ineligible_docs.length) {
				frappe.show_alert({
					message: __("Skipping ineligible Payment Entries:<br><strong>{0}</strong>", [
						ineligible_docs.join(", "),
					]),
					indicator: "yellow",
				});
			}

			frappe.confirm(__("Pay and Submit {0} documents?", [eligible_docs.length]), () => {
				this.disable_list_update = true;

				payment_utils.authenticate_payment_entries(eligible_docs, (auth_id) => {
					pay_and_submit(auth_id, eligible_docs);

					list_view.disable_list_update = false;
					list_view.clear_checked_items();
					list_view.refresh();
				});
			});
		});
	},
};

function is_eligible(doc) {
	return (
		doc.docstatus === 0 &&
		doc.payment_type === "Pay" &&
		doc.paid_from_account_currency === "INR" &&
		doc.mode_of_payment !== "Cash" &&
		doc.make_bank_online_payment &&
		doc.razorpayx_account &&
		doc.razorpayx_payout_status === "Not Initiated"
	);
}

function pay_and_submit(auth_id, docnames, callback = null) {
	const task_id = Math.random().toString(36).slice(-5);
	frappe.realtime.task_subscribe(task_id);

	return frappe
		.xcall(
			"razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.bulk_pay_and_submit",
			{
				auth_id: auth_id,
				docnames: docnames,
				task_id: task_id,
			}
		)
		.then((failed_docnames) => {
			if (failed_docnames?.length) {
				const comma_separated_records = frappe.utils.comma_and(failed_docnames);
				frappe.throw(__("Cannot pay and submit {0}.", [comma_separated_records]));
			}

			if (failed_docnames?.length < docnames.length) {
				frappe.utils.play_sound("submit");
				callback && callback();
			}
		})
		.finally(() => {
			frappe.realtime.task_unsubscribe(task_id);
		});
}
