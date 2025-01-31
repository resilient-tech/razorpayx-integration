frappe.ui.form.on("Payment Entry", {
	bank_account: async function (frm) {
		if (!frm.doc.bank_account) {
			frm.set_value("make_bank_online_payment", 0);
		}
	},

	contact_person: function (frm) {
		if (!frm.doc.contact_person) {
			payment_utils.reset_values(frm, "contact_email", "contact_mobile");
		}
	},
});
