frappe.ui.form.on("Bank Account", {
	setup: function (frm) {
		frm.set_query("contact_to_pay", function () {
			return {
				filters: {
					link_doctype: frm.doc.party_type,
					link_name: frm.doc.party,
				},
			};
		});
	},
});
