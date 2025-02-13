frappe.provide("razorpayx");

const RPX_DOCTYPE = "RazorpayX Integration Setting";
const DESCRIPTION_REGEX = /^[a-zA-Z0-9 ]{1,30}$/;

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

	validate_payout_description(description) {
		if (!description || DESCRIPTION_REGEX.test(description)) return;

		frappe.throw({
			message: __(
				"Must be <strong>alphanumeric</strong> and contain <strong>spaces</strong> only, with a maximum of <strong>30</strong> characters."
			),
			title: __("Invalid RazorpayX Payout Description"),
		});
	},
});
