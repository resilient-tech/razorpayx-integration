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
});
