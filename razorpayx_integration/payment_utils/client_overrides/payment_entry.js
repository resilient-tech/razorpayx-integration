frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		// update descriptions
		frm.get_field("payment_type").set_empty_description();
		frm.get_field("reference_no").set_empty_description();
	},

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
