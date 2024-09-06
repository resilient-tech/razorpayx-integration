frappe.ui.form.on("Payment Entry", {
	// todo: work  on this Date : Thursday, September 05, 2024

	setup: function (frm) {
		frm.set_query("party_type", function () {
			return {
				filters: {
					name: ["in", ["Employee", "Customer", "Supplier"]],
				},
			};
		});

		// todo : left from here CONTINUE FROM HERE Thu, Sep 05, 2024 02:54 pm ....
		frm.add_fetch("party_bank_acc", "bank", "party_bank");
		frm.add_fetch("party_bank_acc", "bank_account_no", "party_bank_ac_no");
		frm.add_fetch("party_bank_acc", "branch_code", "party_bank_branch_code");
	},
});
