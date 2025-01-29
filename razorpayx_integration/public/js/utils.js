frappe.provide("razorpayx");

const RPX_DOCTYPE = "RazorPayX Integration Setting";

Object.assign(razorpayx, {
	RPX_DOCTYPE,

	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},

	async get_razorpayx_setting(bank_account, fields = "name") {
		const response = await frappe.db.get_value(
			RPX_DOCTYPE,
			{ bank_account: bank_account, disabled: 0 },
			fields
		);

		return response.message;
	},
});
