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
				frappe.msgprint(__("Please select proper Payment Entries to pay and submit."));
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

			payment_utils.authenticate_payment_entries(eligible_docs, (auth_id) => {
				pay_and_submit(auth_id, eligible_docs);
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

function pay_and_submit(auth_id, docs) {
	// TODO: Implement the payment and submit logic
	// ! How to pass auth id to the server side?
	/**
	 * References:
	 * https://github.com/frappe/frappe/blob/3eda272bd61b1e73b74d30b1704d885a39c75d0c/frappe/public/js/frappe/list/list_view.js#L1983
	 * https://github.com/frappe/frappe/blob/3eda272bd61b1e73b74d30b1704d885a39c75d0c/frappe/public/js/frappe/list/bulk_operations.js#L275
	 */
}
