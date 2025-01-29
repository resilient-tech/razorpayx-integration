frappe.provide("razorpayx");

const PAYOUT_AUTHORIZER = "Online Payments Authorizer";
const RPX_DOCTYPE = "RazorPayX Integration Setting";
const IMPS_LIMIT = 5_00_000;
const PAY_ICON = "expenses";

Object.assign(razorpayx, {
	PAYOUT_AUTHORIZER,

	RPX_DOCTYPE,

	IMPS_LIMIT,

	PAY_ICON,

	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},

	can_user_authorize_payout() {
		return (
			frappe.user.has_role(razorpayx.PAYOUT_AUTHORIZER) &&
			frappe.perm.has_perm("Payment Entry", 0, "submit")
		);
	},

	async get_razorpayx_setting(bank_account, fields = "name") {
		const response = await frappe.db.get_value(
			razorpayx.RPX_DOCTYPE,
			{ bank_account: bank_account, disabled: 0 },
			fields
		);

		return response.message;
	},
});
