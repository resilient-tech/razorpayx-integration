frappe.ui.form.on("User", {
	refresh: function (frm) {
		if (
			!cint(frappe.boot.sysdefaults.enable_two_factor_auth) ||
			!frappe.user.has_role(payment_utils.PAYOUT_AUTHORIZER) ||
			frappe.session.user != frm.doc.name
		) {
			return;
		}

		frm.add_custom_button(
			__("Reset Payment OTP Secret"),
			function () {
				frappe.call({
					method: "razorpayx_integration.payment_utils.auth.reset_otp_secret",
					args: {
						user: frm.doc.name,
					},
				});
			},
			__("Password")
		);
	},
});
