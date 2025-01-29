frappe.provide("payment_utils");

const PAYOUT_AUTHORIZER = "Online Payments Authorizer";
const IMPS_LIMIT = 5_00_000;
const PAY_ICON = "expenses";

Object.assign(payment_utils, {
	PAYOUT_AUTHORIZER,
	IMPS_LIMIT,
	PAY_ICON,

	can_user_authorize_payout() {
		return frappe.user.has_role(PAYOUT_AUTHORIZER) && frappe.perm.has_perm("Payment Entry", 0, "submit");
	},
});
