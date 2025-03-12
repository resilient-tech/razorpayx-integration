// Copyright (c) 2025, Resilient Tech and contributors
// For license information, please see license.txt

const PAYOUT_STATUS = {
	"Not Initiated": "cyan",
	Queued: "yellow",
	Pending: "yellow",
	Scheduled: "purple",
	Processing: "blue",
	Processed: "green",
	Failed: "red",
	Cancelled: "red",
	Rejected: "red",
	Reversed: "red",
};

const DOC_STATUS = ["Draft", "Submit", "Cancel"];

frappe.query_reports["RazorpayX Payout Status"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "docstatus",
			label: __("Document Status"),
			fieldtype: "MultiSelectList",
			options: DOC_STATUS,
			default: "Submit",
			get_data: function () {
				let options = [];
				for (const status of DOC_STATUS) {
					options.push({
						value: status,
						label: status,
						description: "",
					});
				}
				return options;
			},
		},
		{
			fieldname: "payout_status",
			label: __("Payout Status"),
			fieldtype: "MultiSelectList",
			options: Object.keys(PAYOUT_STATUS),
			get_data: function () {
				let options = [];
				for (const status of Object.keys(PAYOUT_STATUS)) {
					options.push({
						value: status,
						label: status,
						description: "",
					});
				}
				return options;
			},
		},
		{
			fieldname: "payout_via_link",
			label: __("Payout Via Link"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "authorized_by",
			label: __("Authorized By"),
			fieldtype: "Link",
			options: "User",
		},
		// TODO: Add filters for date range
	],
};
