frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		// update descriptions
		frm.get_field("payment_type").set_empty_description();
		frm.get_field("reference_no").set_empty_description();
	},

	validate: function (frm) {
		if (!frm.doc.make_bank_online_payment) return;

		if (frm.doc.bank_payment_mode === payment_utils.BANK_PAYMENT_MODE.LINK) {
			if (!frm.doc.contact_mobile && !frm.doc.contact_email) {
				let msg = "";

				if (frm.doc.party_type === "Employee") {
					msg = __("Set Employee's Mobile or Preferred Email to make payout with link.");
				} else {
					msg = __("Any one of Party's Mobile or Email is mandatory to make payout with link.");
				}

				frappe.throw({ message: msg, title: __("Contact Details Missing") });
			}
		}

		// TODO: CHECK FOR MODE LIMIT AND MINIMUM AMOUNT
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

	party_bank_account: function (frm) {
		if (!frm.doc.party_bank_account) {
			frm.set_value("bank_payment_mode", payment_utils.BANK_PAYMENT_MODE.LINK);
		} else {
			frm.set_value("bank_payment_mode", payment_utils.BANK_PAYMENT_MODE.NEFT);
		}
	},

	contact_person: function (frm) {
		if (!frm.doc.contact_person && frm.doc.contact_mobile) {
			frm.set_value("contact_mobile", "");
		}
	},
});
