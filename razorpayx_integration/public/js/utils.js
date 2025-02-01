frappe.provide("razorpayx");

const RPX_DOCTYPE = "RazorpayX Integration Setting";

Object.assign(razorpayx, {
	RPX_DOCTYPE,

	async get_razorpayx_setting(bank_account, fields = "name") {
		const response = await frappe.db.get_value(
			RPX_DOCTYPE,
			{ bank_account: bank_account, disabled: 0 },
			fields
		);

		return response.message;
	},

	is_payout_via_razorpayx(doc) {
		return (
			doc.make_bank_online_payment && doc.integration_doctype === RPX_DOCTYPE && doc.integration_docname
		);
	},
});
