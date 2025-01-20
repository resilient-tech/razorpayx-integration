// Copyright (c) 2024, Resilient Tech and contributors
// For license information, please see license.txt

const WEBHOOK_PATH = "razorpayx_integration.razorpayx_integration.utils.webhook.razorpayx_webhook_listener";

frappe.listview_settings["RazorPayX Integration Setting"] = {
	refresh: function (list_view) {
		const copy_icon = frappe.utils.icon("clipboard");

		list_view.page.add_inner_button(__("{0} Copy Webhook", [copy_icon]), function () {
			const webhook = `${frappe.urllib.get_base_url()}/api/method/${WEBHOOK_PATH}`;
			frappe.utils.copy_to_clipboard(webhook);
		});
	},
};
