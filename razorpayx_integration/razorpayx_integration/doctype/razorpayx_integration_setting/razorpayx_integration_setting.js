// Copyright (c) 2024, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("RazorPayX Integration Setting", {
	setup: function (frm) {
		frm.set_query("bank_account", function () {
			return {
				filters: {
					is_company_account: 1,
					disabled: 0,
				},
			};
		});
	},

	onload: function (frm) {
		if (!frm.is_new()) return;

		frm.set_intro(
			__(
				`Get RazorPayX API's Key <strong>ID</strong> and <strong>Secret</strong> from
					<a target="_blank" href="https://x.razorpay.com/settings/developer-controls">
						here {0}
					</a>
				if not available.`,
				[frappe.utils.icon("link-url")]
			)
		);
	},

	after_save: function (frm) {
		if (frm.doc.webhook_secret) return;

		frappe.show_alert({
			message: __("Webhook Secret is missing! <br> You will not receive any updates!"),
			indicator: "orange",
		});
	},
});
