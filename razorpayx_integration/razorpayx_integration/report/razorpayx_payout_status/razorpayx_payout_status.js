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

const DOC_STATUS = { Draft: "grey", Submit: "blue", Cancel: "red" };

const TIMESPANS = [
	"This Week",
	"This Month",
	"This Quarter",
	"This Year",
	"Last Week",
	"Last Month",
	"Last Quarter",
	"Last Year",
	"Select Date Range",
];

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
			fieldname: "time_span",
			label: __("Time Span"),
			fieldtype: "Select",
			options: TIMESPANS,
			default: "This Month",
			reqd: 1,
			on_change: (report) => {
				if (report.get_filter_value("time_span") === "Select Date Range") {
					const date_range = report.get_filter("date_range");
					date_range.df.reqd = 1;
					date_range.set_required(1);
					date_range.refresh();
				}
			},
		},
		{
			fieldname: "date_range",
			fieldtype: "DateRange",
			label: __("Date Range"),
			depends_on: "eval: doc.time_span === 'Select Date Range'",
			default: [frappe.datetime.month_start(), frappe.datetime.now_date()],
		},
		{
			fieldname: "docstatus",
			label: __("Document Status"),
			fieldtype: "MultiSelectList",
			get_data: () => get_multiselect_options(Object.keys(DOC_STATUS)),
		},
		{
			fieldname: "payout_status",
			label: __("Payout Status"),
			fieldtype: "MultiSelectList",
			get_data: () => get_multiselect_options(Object.keys(PAYOUT_STATUS)),
		},
		{
			fieldname: "payout_mode",
			label: __("Payout Mode"),
			fieldtype: "MultiSelectList",
			get_data: () =>
				get_multiselect_options(Object.values(payment_integration_utils.PAYMENT_TRANSFER_METHOD)),
		},
		{
			fieldname: "razorpayx_config",
			label: __("RazorpayX Configuration"),
			fieldtype: "Link",
			options: "RazorpayX Configuration",
			get_query: function () {
				return {
					filters: { company: frappe.query_report.get_filter_value("company") },
				};
			},
		},
		{
			fieldname: "payout_made_by",
			label: __("Payout Made By"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "ignore_amended",
			label: __("Ignore Amended"),
			fieldtype: "Check",
		},
	],

	onload: (report) => {
		const docstatus = report.get_filter("docstatus");

		if (docstatus && (!docstatus.get_value() || docstatus.get_value().length === 0)) {
			docstatus.set_value("Submit");
		}
	},
};

function get_multiselect_options(values) {
	const options = [];
	for (const option of values) {
		options.push({
			value: option,
			label: option,
			description: "",
		});
	}
	return options;
}
