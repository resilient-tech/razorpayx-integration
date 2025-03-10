frappe.provide("razorpayx");

const RAZORPAYX_CONFIG = "RazorpayX Configuration";
const DESCRIPTION_REGEX = /^[a-zA-Z0-9 ]{1,30}$/;

Object.assign(razorpayx, {
	RAZORPAYX_CONFIG,

	async get_razorpayx_config(bank_account, fields = "name") {
		const response = await frappe.db.get_value(
			RAZORPAYX_CONFIG,
			{ bank_account: bank_account, disabled: 0 },
			fields
		);

		return response.message;
	},

	is_payout_via_razorpayx(doc) {
		return (
			doc.make_bank_online_payment &&
			doc.integration_doctype === RAZORPAYX_CONFIG &&
			doc.integration_docname
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
