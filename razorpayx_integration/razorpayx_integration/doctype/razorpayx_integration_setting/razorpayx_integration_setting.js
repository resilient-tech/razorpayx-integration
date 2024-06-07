// Copyright (c) 2024, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("RazorPayX Integration Setting", {
  onload: function (frm) {
    if (frm.is_new()) {
      const intro_msg = `Get RazorPayX API's Key <strong>Id</strong> and <strong>Secret</strong> from
							<a target="_blank" href="https://x.razorpay.com/settings/developer-controls">
								here ${frappe.utils.icon("link-url")}
							</a>
							if not available.`;
      frm.set_intro(__(intro_msg));
    }
  },
});
