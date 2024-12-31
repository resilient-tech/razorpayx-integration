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
});

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
