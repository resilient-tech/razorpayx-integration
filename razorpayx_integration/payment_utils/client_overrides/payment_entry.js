const TRANSFER_METHOD = payment_utils.PAYMENT_TRANSFER_METHOD;

frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		// update descriptions
		frm.get_field("payment_type").set_empty_description();
		frm.get_field("reference_no").set_empty_description();
	},

	validate: function (frm) {
		if (!frm.doc.integration_doctype || !frm.doc.integration_docname) {
			if (frm.doc.make_bank_online_payment) {
				frm.set_value("make_bank_online_payment", 0);
			}

			return;
		}

		if (!frm.doc.make_bank_online_payment) return;

		if (frm.doc.payment_transfer_method === TRANSFER_METHOD.LINK) {
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

		payment_utils.validate_payment_transfer_method(frm.doc.payment_transfer_method, frm.doc.paid_amount);
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
			frm.set_value("payment_transfer_method", TRANSFER_METHOD.LINK);
		} else {
			frm.set_value("payment_transfer_method", TRANSFER_METHOD.NEFT);
		}
	},

	contact_person: function (frm) {
		if (!frm.doc.contact_person && frm.doc.contact_mobile) {
			frm.set_value("contact_mobile", "");
		}
	},
});
