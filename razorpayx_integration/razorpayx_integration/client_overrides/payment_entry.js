// TODO: update Party Bank Account filters
// TODO: show it will pay by razorpayx
// TODO: RazorpayX status fields also allow for edit after submit
// TODO: Backend validation for RazorpayX status fields !!!

// TODO: Update CF and CP for Payment Entry
// TODO: Work with new design for Payment Entry ???
// TODO: Improve UX and UI for Payment Entry

// TODO: for UX: change submit button label to `Pay and Submit`
// TODO: Button to create RazorpayX payout after submit if not paid by RazorpayX

const PAYOUT_FIELDS = [
	//  Common
	"payment_type",
	"bank_account",
	// Party related
	"party",
	"party_type",
	"party_name",
	"party_bank_account",
	"party_bank_account_no",
	"party_bank_ifsc",
	"party_upi_id",
	"contact_person",
	"contact_mobile",
	"contact_email",
	// RazorpayX Related
	"paid_amount",
	"razorpayx_account",
	"make_bank_online_payment",
	"razorpayx_payout_mode",
	"razorpayx_payout_desc",
	"razorpayx_payout_status",
	"razorpayx_pay_instantaneously",
	"razorpayx_payout_id",
	"razorpayx_payout_link_id",
];

const RAZORPAYX_DOCTYPE = "RazorPayX Integration Setting";

frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		// Do not allow to edit fields if Payment is processed by RazorpayX in amendment
		disable_payout_fields_in_amendment(frm);

		// set Intro for Payment
		if (frm.is_new() || !frm.doc.make_bank_online_payment) return;

		if (frm.doc.docstatus == 0) {
			frm.set_intro(__("This Payment will be processed by RazorpayX on submission."));
		} else if (frm.doc.docstatus == 1) {
			frm.set_intro(
				__("RazorPayX Payout Status: <strong>{0}</strong>", [frm.doc.razorpayx_payout_status])
			);
		}
	},

	bank_account: async function (frm) {
		// fetch razorpayx_integration account
		if (!frm.doc.bank_account) {
			frm.set_value("razorpayx_account", "");
		} else {
			const response = await frappe.db.get_value(
				"RazorPayX Integration Setting",
				{
					bank_account: frm.doc.bank_account,
				},
				"name"
			);

			const { name } = response.message || {};

			frm.set_value("razorpayx_account", name);
		}
	},

	before_cancel: async function (frm) {
		if (!frm.doc.make_bank_online_payment) return;

		// Check Payout is cancellable or not
		if (!can_cancel_payout(frm)) {
			frappe.throw({
				message: __("Payment Entry cannot be cancelled as Payout is already in {0} state.", [
					frm.doc.razorpayx_payout_status,
				]),
				title: __("Cannot Cancel Payment Entry"),
			});
		}

		const auto_cancel_payout = await should_auto_cancel_payout(frm);
		if (auto_cancel_payout) return;

		frappe.validate = false;

		return new Promise((resolve) => {
			const continue_cancellation = () => {
				frappe.validate = true;
				resolve();
			};

			return show_cancel_payout_dialog(frm, continue_cancellation);
		});
	},
});

/**
 * Check if the payout can be cancelled or not related to the Payment Entry.
 * @param {object} frm The doctype's form object
 * @returns {boolean} `true` if the payout can be cancelled, otherwise `false`
 */
function can_cancel_payout(frm) {
	return (
		frm.doc.make_bank_online_payment &&
		["Not Initiated", "Queued"].includes(frm.doc.razorpayx_payout_status)
	);
}

/**
 * Get the value of `auto_cancel_payout` field from RazorpayX Integration Setting
 * based on the selected RazorpayX Account.
 * @param {object} frm The doctype's form object
 * @returns {Promise<boolean>} The value of `auto_cancel_payout
 */
async function should_auto_cancel_payout(frm) {
	const response = await frappe.db.get_value(
		RAZORPAYX_DOCTYPE,
		frm.doc.razorpayx_account,
		"auto_cancel_payout"
	);

	return response.message?.auto_cancel_payout || 0;
}

/**
 * Show dialog to confirm the cancellation of payout.
 *
 * Two options are available:
 * 1. Do not cancel the payout.
 * 2. Cancel the payout.
 *
 * @param {object} frm The doctype's form object
 * @param {function} callback The function to call after confirmation
 */
function show_cancel_payout_dialog(frm, callback) {
	const dialog = new frappe.ui.Dialog({
		title: __("Cancel Payment Entry with Payout"),
		fields: [
			{
				fieldname: "cancel_payout",
				label: __("Cancel Payout"),
				fieldtype: "Check",
				default: 1,
				description: __(
					"This will cancel the payout and payout link for this Payment Entry if checked."
				),
			},
		],
		primary_action_label: __("Continue"),
		primary_action: async (values) => {
			if (values.cancel_payout) {
				await frappe.call({
					method: "YOUR_API_METHOD",
					args: {
						doctype: frm.doctype,
						docname: frm.docname,
					},
				});

				frm.refresh();
			}

			callback && callback();
			dialog.hide();
		},
	});

	// Make primary action button Background Red
	dialog.get_primary_btn().removeClass("btn-primary").addClass("btn-danger");
	dialog.show();
}

/**
 * If current Payment Entry is amended from another Payment Entry,
 * and source Payment Entry is processed by RazorPayX, then disable
 * payout fields in the current Payment Entry.
 *
 * @param {object} frm The doctype's form object
 */
async function disable_payout_fields_in_amendment(frm) {
	if (!frm.doc.amended_from) return;

	let disable_payout_fields = frm.doc.__onload?.disable_payout_fields;

	if (disable_payout_fields === undefined) {
		const response = await frappe.db.get_value(
			"Payment Entry",
			frm.doc.amended_from,
			"make_bank_online_payment"
		);

		disable_payout_fields = response.message?.make_bank_online_payment || 0;
	}

	frm.toggle_enable(PAYOUT_FIELDS, disable_payout_fields ? 0 : 1);
}
