frappe.provide("razorpayx_integration");

// todo: make it easy  (Ref: https://github.com/resilient-tech/bank_integration/blob/edb06993e9257d6cfbc377242f3ef9051dc9fd50/bank_integration/public/js/common.js#L4)
Object.assign(razorpayx_integration, {
	get_date_in_user_fmt(date) {
		return frappe.datetime.str_to_user(date, null, frappe.datetime.get_user_date_fmt());
	},
});
