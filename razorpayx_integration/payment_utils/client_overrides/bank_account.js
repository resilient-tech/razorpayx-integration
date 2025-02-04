// Copyright (c) 2025, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Account", {
	after_save: function (frm) {
		if (!frm.doc.is_company_account && (!frm.doc.party || !frm.doc.party_type)) {
			frappe.msgprint({
				message: __(
					"This bank account will not be used by <strong>RazorpayX</strong> as it is neither a company account nor a party account."
				),
				title: __("Warning"),
				indicator: "yellow",
			});
		}
	},
});
