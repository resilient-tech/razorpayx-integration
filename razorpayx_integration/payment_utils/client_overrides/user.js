frappe.ui.form.on("User", {
	refresh: function (frm) {
		if (
			!is_2fa_otp_app_enabled() ||
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

function is_2fa_otp_app_enabled() {
	return (
		cint(frappe.boot.sysdefaults.enable_two_factor_auth) &&
		frappe.boot.sysdefaults.two_factor_method === payment_utils.AUTH_METHODS.OTP_APP
	);
}
