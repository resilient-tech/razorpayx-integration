// Copyright (c) 2025, Resilient Tech and contributors
// For license information, please see license.txt

frappe.listview_settings["Payment Entry"] = {
	add_fields: [
		"make_bank_online_payment",
		"integration_docname",
		"integration_doctype",
		"razorpayx_payout_status",
	],

	onload: function (list_view) {
		// Add `Pay and Submit` button to the Payment Entry list view
		if (!payment_integration_utils.can_user_authorize_payment()) return;

		list_view.page.add_actions_menu_item(__("Pay and Submit"), () => {
			const selected_docs = list_view.get_checked_items();
			const marked_docs = [];
			const unmarked_docs = [];
			const ineligible_docs = [];

			selected_docs.forEach((doc) => {
				if (can_make_payout_via_razorpayx(doc)) {
					if (doc.make_bank_online_payment) marked_docs.push(doc.name);
					else unmarked_docs.push(doc.name);
				} else {
					ineligible_docs.push(doc.name);
				}
			});

			if (!marked_docs.length && !unmarked_docs.length) {
				frappe.msgprint(
					__("Please select proper payment entries to pay and submit."),
					__("Invalid Selection")
				);
				return;
			}

			show_pay_and_submit_dialog(list_view, marked_docs, unmarked_docs, ineligible_docs);
		});
	},
};

function can_make_payout_via_razorpayx(doc) {
	return (
		doc.docstatus === 0 &&
		doc.payment_type === "Pay" &&
		doc.paid_from_account_currency === "INR" &&
		doc.razorpayx_payout_status === "Not Initiated" &&
		doc.integration_doctype === razorpayx.RPX_DOCTYPE &&
		doc.integration_docname
	);
}

function show_pay_and_submit_dialog(list_view, marked_docs, unmarked_docs, ineligible_docs) {
	const dialog = new frappe.ui.Dialog({
		title: __("Confirm Payment Entries"),
		primary_action_label: __("{0} Pay and Submit", [
			frappe.utils.icon(payment_integration_utils.PAY_ICON),
		]),
		fields: [
			{
				fieldname: "unmarked_doc_sec_break",
				fieldtype: "Section Break",
				depends_on: `eval: ${unmarked_docs.length > 0}`,
			},
			{
				fieldname: "unmarked_doc_html",
				fieldtype: "HTML",
				options: get_docs_html(unmarked_docs, __("Payment entries not marked for online payment")),
			},
			{
				fieldname: "unmarked_doc_sec_break",
				fieldtype: "Section Break",
				depends_on: `eval: ${unmarked_docs.length > 0}`,
			},
			{
				fieldname: "mark_online_payment",
				label: __("Allow to make online payment"),
				fieldtype: "Check",
				default: unmarked_docs.length ? 1 : 0,
				description: `<p class='text-warning font-weight-bold'>
								${__("If unchecked, above payment entries will be skipped!")}
							</p>`,
			},
			{
				fieldname: "marked_cb_break",
				fieldtype: "Column Break",
			},
			{
				fieldname: "description",
				label: __("Payout Description"),
				fieldtype: "Data",
				description: __("For above payment entries only."),
				depends_on: `eval: ${unmarked_docs.length > 0} && doc.mark_online_payment`,
			},
			{
				fieldname: "marked_doc_sec_break",
				fieldtype: "Section Break",
				depends_on: `eval: ${marked_docs.length > 0}`,
			},
			{
				fieldname: "marked_doc_html",
				fieldtype: "HTML",
				options: get_docs_html(marked_docs, __("Eligible payment entries to be pay and submit")),
			},
			{
				fieldname: "ineligible_doc_sec_break",
				fieldtype: "Section Break",
				depends_on: `eval: ${ineligible_docs.length > 0}`,
			},
			{
				fieldname: "ineligible_doc_html",
				fieldtype: "HTML",
				options: get_docs_html(ineligible_docs, __("Ineligible payment entries to be skipped")),
			},
		],

		primary_action: (values) => {
			razorpayx.validate_payout_description(values.description);

			dialog.hide();

			list_view.disable_list_update = true;

			if (!marked_docs.length && (!unmarked_docs.length || !values.mark_online_payment)) {
				reset_list_view(list_view);
				frappe.show_alert(__("No payment entries to pay and submit."));
				return;
			}

			payment_integration_utils.authenticate_payment_entries(
				[...marked_docs, ...unmarked_docs],
				(auth_id) => {
					// Reference: https://github.com/frappe/frappe/blob/3eda272bd61b1e73b74d30b1704d885a39c75d0c/frappe/public/js/frappe/list/list_view.js#L1983
					pay_and_submit(
						auth_id,
						marked_docs,
						unmarked_docs,
						values.mark_online_payment,
						values.description
					);

					reset_list_view(list_view);
				}
			);
		},
	});

	dialog.show();
}

function get_docs_html(docs, text) {
	if (!docs.length) return "";

	function get_formlink(doc) {
		return `<a target="_blank" href="${frappe.utils.get_form_link("Payment Entry", doc)}">${doc}</a>`;
	}

	return `<details>
				<summary>${text} (${docs.length}):</summary>
				<ol>${docs.map((doc) => `<li>${get_formlink(doc)}</li>`).join("")}</ol>
			</details>
	`;
}

function reset_list_view(list_view) {
	list_view.disable_list_update = false;
	list_view.clear_checked_items();
	list_view.refresh();
}

function pay_and_submit(
	auth_id,
	marked_docnames,
	unmarked_docnames = null,
	mark_online_payment = true,
	description = null,
	callback = null
) {
	// Reference: https://github.com/frappe/frappe/blob/3eda272bd61b1e73b74d30b1704d885a39c75d0c/frappe/public/js/frappe/list/bulk_operations.js#L275
	const task_id = Math.random().toString(36).slice(-5);
	frappe.realtime.task_subscribe(task_id);

	if (!unmarked_docnames.length || !mark_online_payment) unmarked_docnames = [];

	frappe.show_alert({
		message: __("Pay and Submitting {0} Payment Entries...", [
			marked_docnames.length + unmarked_docnames.length,
		]),
		indicator: "blue",
	});

	return frappe
		.xcall(
			"razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.bulk_pay_and_submit",
			{
				auth_id: auth_id,
				marked_docnames: marked_docnames,
				unmarked_docnames: unmarked_docnames,
				mark_online_payment: mark_online_payment,
				description: description,
				task_id: task_id,
			}
		)
		.then((failed_docnames) => {
			if (failed_docnames?.length) {
				const comma_separated_records = frappe.utils.comma_and(failed_docnames);
				frappe.throw(__("Cannot pay and submit {0}.", [comma_separated_records]));
			}

			frappe.utils.play_sound("submit");
			callback && callback();
		})
		.finally(() => {
			frappe.realtime.task_unsubscribe(task_id);
		});
}
