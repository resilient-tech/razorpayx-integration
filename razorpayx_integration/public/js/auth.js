frappe.provide("payment_utils");

const AUTH_METHODS = {
	AUTHENTICATOR_APP: "authenticator_app",
	SMS: "sms",
	EMAIL: "email",
	PASSWORD: "password",
};

Object.assign(payment_utils, {
	AUTH_METHODS,

	async authenticate_otp(payment_entries, callback) {
		const authentication = await this.generate_otp(payment_entries);
		if (!authentication) return;

		const { title, fields } = this.get_authentication_dialog_details(authentication);

		const dialog = new frappe.ui.Dialog({
			title: title,
			fields: fields,
			primary_action_label: __("Authenticate"),
			primary_action: async (values) => {
				const { verified, msg } = await this.verify_otp(values.authenticator, authentication.temp_id);

				// Invalid OTP or Password
				if (!verified) {
					const description = `<div class="text-danger font-weight-bold">
											${frappe.utils.icon("solid-error")}
											${__(msg || "Invalid! Please try again.")}
										</div>`;

					dialog.get_field("authenticator").set_new_description(description);
					dialog.set_value("authenticator", "");
					// TODO: also remove description when starting to type
					return;
				}

				dialog.close();

				callback && callback(authentication.temp_id);
			},
		});

		dialog.show();
	},

	async verify_otp(otp, temp_id) {
		/*
		Verify the OTP for the payment entries.

		If 2 factor is on then,
		- verify OTP
		- return verified status

		If 2 factor is off then,
		- Wait for password
		- Authenticate user
		- OTP is not verified

		returns like:

		{
			verified: false,
			msg: "Invalid OTP"

		}
		*/
		// calling API
		// const response = await frappe.call("METHOD", { otp, temp_id });
		// return response?.message;

		// TODO: remove~ : Fake response
		return {
			verified: false,
			msg: "Invalid OTP",
		};
	},

	async generate_otp(payment_entries) {
		/*
		Generate and send OTP for the payment entries.

		If 2 factor is on then,
		- generate OTP
		- send OTP to user
		- authentication method:
			- OTP App
			- SMS
			- Email

		If 2 factor is off then,
		- Wait for password
		- Authenticate user
		- OTP is not generated or sent

		returns like:

		{
			temp_id: "4656486620",
			verification: {
				method: "otp",
				message: "OTP sent to your mobile number" (Optional)
			}

		}
		*/

		// calling API
		// const response = await frappe.call("METHOD", { payment_entries });
		// return response?.message;

		// TODO: remove~ : Fake response
		return {
			temp_id: "4656486620",
			verification: {
				method: this.AUTH_METHODS.SMS,
				message: "OTP sent to your mobile number",
			},
		};
	},

	// ++++++++++ HELPERS ++++++++++ //
	get_authentication_dialog_details(authentication) {
		const get_description = (desc) => __(authentication.verification?.message || desc);

		const data = {
			label: __("OTP"),
			fieldtype: "Data",
		};

		switch (authentication.verification.method) {
			case this.AUTH_METHODS.AUTHENTICATOR_APP:
				data.title = __("Authenticate using OTP App");
				data.description = get_description("Enter Code displayed in OTP App");
				break;
			case this.AUTH_METHODS.SMS:
				data.title = __("Authenticate using SMS");
				data.description = get_description("Enter OTP sent to your mobile number");
				break;
			case this.AUTH_METHODS.EMAIL:
				data.title = __("Authenticate using Email");
				data.description = get_description("Enter OTP sent to your email address");
				break;
			case this.AUTH_METHODS.PASSWORD:
				data.title = __("Authenticate using Password");
				data.description = get_description("Enter your user password");
				data.fieldtype = "Password";
				break;
		}

		return {
			title: data.title,
			fields: [
				{
					fieldname: "authenticator",
					fieldtype: data.fieldtype,
					label: data.label,
					reqd: 1,
					description: data.description,
				},
			],
		};
	},
});

let otp_app = function (setup) {
	let desc = "";
	if (setup) desc = __("Enter Code displayed in OTP App");
	else desc = __("OTP setup using OTP App was not completed. Please contact your Administrator");
};
