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

	refresh: function (frm) {
		const workflow_state = frm.doc?.razorpayx_workflow_state;
		const final_states = ["Approved", "Cancelled", "Rejected"];

		if (final_states.includes(workflow_state)) {
			frm.disable_form();
		}
	},
});
