// Copyright (c) 2024, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('RazorPayX Integration Setting', {
	onload: function (frm) {
		if (frm.is_new()) {
			const intro_msg = `Get <b>RazorPayX</b> API's Key <i>Id</i> and <i>Secret</i> from 
							<a target="_blank" href="https://x.razorpay.com/settings/developer-controls"><b>here</b><a/> 
							if not available.`;
			frm.set_intro(__(intro_msg))
		}
	}
});
