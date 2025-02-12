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

	party: async function (frm) {
		if (frm.doc.contact_mobile) frm.set_value("contact_mobile", "");

		if (frm.doc.party_type !== "Employee" || !frm.doc.party) return;

		const details = await payment_utils.get_employee_contact_details(frm.doc.party);

		if (details) frm.set_value(details);
	},

	contact_person: function (frm) {
		if (!frm.doc.contact_person && frm.doc.contact_mobile) {
			frm.set_value("contact_mobile", "");
		}
	},
});
