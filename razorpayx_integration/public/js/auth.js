const { callback } = require("chart.js/helpers");

frappe.provide("payment_utils");

Object.assign(payment_utils, {
	async authenticate_otp(payment_entries, callback) {
		const { message } = await this.generate_otp();

		// verfication object in message {method: "otp", message}

		let desc = __("Please enter the OTP sent to your mobile number");
		const d = new frappe.ui.Dialog({
			title: __("Authenticate OTP"),
			fields: [
				{
					fieldname: "otp",
					fieldtype: "Data",
					label: __("OTP"),
					reqd: 1,
					description: desc,
				},
			],
			primary_action_label: __("Verify"),
			primary_action: async (values) => {
				await this.verify_otp(values.otp, message.temp_id);
				d.close();

				callback && callback(message.temp_id);
			},
		});

		d.show();
	},

	async verify_otp(otp, temp_id) {},

	async generate_otp() {
		// user and payment entries
	},
});

let otp_app = function (setup) {
	let desc;
	if (setup) desc = __("Enter Code displayed in OTP App");
	else desc = __("OTP setup using OTP App was not completed. Please contact your Administrator");
};
