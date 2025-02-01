frappe.provide("payment_utils");

const PAYOUT_AUTHORIZER = "Online Payments Authorizer";
const IMPS_LIMIT = 5_00_000;
const PAY_ICON = "expenses";

Object.assign(payment_utils, {
	PAYOUT_AUTHORIZER,
	IMPS_LIMIT,
	PAY_ICON,

	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},

	can_user_authorize_payout() {
		return frappe.user.has_role(PAYOUT_AUTHORIZER) && frappe.perm.has_perm("Payment Entry", 0, "submit");
	},

	set_onload(frm, key, value) {
		if (!frm.doc.__onload) {
			frm.doc.__onload = {};
		}

		frm.doc.__onload[key] = value;
	},

	reset_values(frm, ...fields) {
		fields.forEach((field) => frm.set_value(field, ""));
	},
});
