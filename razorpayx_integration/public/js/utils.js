frappe.provide("razorpayx_integration");

Object.assign(razorpayx_integration, {
	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},
});
