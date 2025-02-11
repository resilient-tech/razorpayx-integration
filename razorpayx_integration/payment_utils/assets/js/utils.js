frappe.provide("payment_utils");

const PAYMENT_AUTHORIZER = "Online Payments Authorizer";
const PAY_ICON = "expenses";
const PAYMENT_TRANSFER_METHOD = {
	NEFT: "NEFT",
	IMPS: "IMPS",
	RTGS: "RTGS",
	UPI: "UPI",
	LINK: "Link",
};

Object.assign(payment_utils, {
	PAYMENT_AUTHORIZER,
	PAYMENT_TRANSFER_METHOD,
	PAY_ICON,

	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},

	can_user_authorize_payment() {
		return (
			frappe.session.user !== "Administrator" &&
			frappe.user.has_role(PAYMENT_AUTHORIZER) &&
			frappe.perm.has_perm("Payment Entry", 0, "submit")
		);
	},

	set_onload(frm, key, value) {
		if (!frm.doc.__onload) {
			frm.doc.__onload = {};
		}

		frm.doc.__onload[key] = value;
	},

	get_onload(frm, key) {
		return frm.doc && frm.doc.__onload ? frm.doc.__onload[key] : undefined;
	},

	reset_values(frm, ...fields) {
		fields.forEach((field) => frm.set_value(field, ""));
	},

	async get_employee_contact_details(employee) {
		const { message } = await frappe.db.get_value("Employee", employee, [
			"cell_number as contact_mobile",
			"prefered_email as contact_email",
		]);

		return message;
	},

	validate_payment_transfer_method(method, amount) {
		if ([PAYMENT_TRANSFER_METHOD.NEFT, PAYMENT_TRANSFER_METHOD.LINK].includes(method)) return;

		if (method === PAYMENT_TRANSFER_METHOD.IMPS && amount > 5_00_000) {
			frappe.throw({
				message: __("Amount should be less than {0} for <strong>{1}</strong> transfer", [
					format_currency(5_00_000, "INR"),
					PAYMENT_TRANSFER_METHOD.IMPS,
				]),
				title: __("Amount Limit Exceeded"),
			});
		} else if (method === PAYMENT_TRANSFER_METHOD.UPI && amount > 1_00_000) {
			frappe.throw({
				message: __("Amount should be less than {0} for <strong>{1}</strong> transfer", [
					format_currency(1_00_000, "INR"),
					PAYMENT_TRANSFER_METHOD.UPI,
				]),
				title: __("Amount Limit Exceeded"),
			});
		} else if (method === PAYMENT_TRANSFER_METHOD.RTGS && amount < 2_00_000) {
			frappe.throw({
				message: __("Amount should be greater than {0} for <strong>{1}</strong> transfer", [
					format_currency(2_00_000, "INR"),
					PAYMENT_TRANSFER_METHOD.RTGS,
				]),
				title: __("Insufficient Amount"),
			});
		}
	},
});
