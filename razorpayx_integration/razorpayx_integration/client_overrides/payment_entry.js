// TODO: update Party Bank Account filters
// TODO: show it will pay by razorpayx
// TODO: RazorpayX status fields also allow for edit after submit
// TODO: Backend validation for RazorpayX status fields !!!

frappe.ui.form.on("Payment Entry", {
	setup: function (frm) {},

	refresh: function (frm) {},

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
