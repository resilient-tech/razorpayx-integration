// TODO: update Party Bank Account filters
// TODO: show it will pay by razorpayx
// TODO: RazorpayX status fields also allow for edit after submit
// TODO: Backend validation for RazorpayX status fields !!!

// TODO: Update CF and CP for Payment Entry
// TODO: Work with new design for Payment Entry ???
// TODO: Improve UX and UI for Payment Entry

// TODO: for UX: change submit button label to `Pay and Submit`
// TODO: Button to create RazorpayX payout after submit if not paid by RazorpayX

frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
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
