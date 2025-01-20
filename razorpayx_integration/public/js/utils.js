frappe.provide("rpx");

const PAYOUT_AUTHORIZER = "RazorPayX Payout Authorizer";
const RPX_DOCTYPE = "RazorPayX Integration Setting";
const IMPS_LIMIT = 5_00_000;
const PAY_ICON = "expenses";

Object.assign(rpx, {
	PAYOUT_AUTHORIZER,

	RPX_DOCTYPE,

	IMPS_LIMIT,

	PAY_ICON,

	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},

	/**
	 * Checking that current user have sufficient permission to make payout.
	 *
	 * @param {string | null} payment_entry - Payment Entry name
	 * @param {string | null} razorpayx_account - RazorPayX Account name
	 * @param {string} pe_permission - Permission to check in Payment Entry
	 * @param {boolean} raise_error - Raise error if permission is not available
	 *
	 */
	user_has_payout_permissions(
		payment_entry = "",
		razorpayx_account = "",
		pe_permission = "submit",
		raise_error = false
	) {
		// this role have permission to read integration settings and submission/cancellation of payment entry
		const has_role = frappe.user.has_role(PAYOUT_AUTHORIZER);
		const has_rpx_permission = frappe.perm.has_perm(RPX_DOCTYPE, 0, "read", razorpayx_account);
		const has_pe_permission = frappe.perm.has_perm("Payment Entry", 7, pe_permission, payment_entry);

		const has_permission = has_role && has_rpx_permission && has_pe_permission;

		if (raise_error && !has_permission) {
			frappe.throw({
				title: __("Insufficient Permissions"),
				message: __("You do not have sufficient permissions to make payout."),
			});
		}

		return has_permission;
	},
});
