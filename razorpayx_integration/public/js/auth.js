frappe.provide("payment_utils");

const AUTH_METHODS = {
	OTP_APP: "OTP App",
	SMS: "SMS",
	EMAIL: "Email",
	PASSWORD: "Password",
};

const BASE_AUTH_PATH = "razorpayx_integration.payment_utils.auth";

Object.assign(payment_utils, {
	AUTH_METHODS,

	/**
	 * Authenticate payment entries using OTP or Password
	 *
	 * It generates OTP for the given payment entries and opens
	 * a dialog to authenticate using OTP or Password.
	 *
	 * Note: Only single OTP is generated for all the payment entries.
	 *
	 * @param {string | string[]} payment_entries - Payment Entry name or list of names
	 * @param {Function} callback - Callback function to be executed after successful authentication
	 */
	async authenticate_otp(payment_entries, callback) {
		if (typeof payment_entries === "string") {
			payment_entries = [payment_entries];
		}

		const generation_details = await this.generate_otp(payment_entries);
		if (!generation_details) return;

		const { title, fields } = this.get_authentication_dialog_details(generation_details);

		const dialog = new frappe.ui.Dialog({
			title: title,
			fields: fields,
			primary_action_label: __("Authenticate"),
			primary_action: async (values) => {
				const { verified, message } = await this.verify_otp(
					values.authenticator,
					generation_details.auth_id
				);

				if (verified) {
					dialog.hide();

					callback && callback(generation_details.auth_id);
					return;
				}

				// Invalid OTP or Password
				const error = `<p class="text-danger font-weight-bold">
									${frappe.utils.icon("solid-error")} &nbsp;
									${__(message || "Invalid! Please try again.")}
								</p>`;

				const auth_field = dialog.get_field("authenticator");
				auth_field.set_new_description(error);

				// reset the description to the original
				setTimeout(() => {
					auth_field.set_new_description(auth_field.df.description);
				}, 3000);
			},
		});

		dialog.show();

		if (this.AUTH_METHODS.PASSWORD === generation_details.method) {
			dialog.get_field("authenticator").disable_password_checks();
		}
	},

	/**
	 * Verify the OTP for the given auth_id.
	 *
	 * @param {string} authenticator OTP or Password
	 * @param {string} auth_id Authentication ID
	 *
	 * ---
	 * Example Response:
	 * ```js
	 * {
	 * 	verified: true,
	 * 	msg: "OTP verified successfully.",
	 * }
	 * ```
	 */
	async verify_otp(authenticator, auth_id) {
		const response = await frappe.call(`${BASE_AUTH_PATH}.verify_otp`, {
			otp: authenticator,
			auth_id: auth_id,
		});

		return response?.message;
	},

	/**
	 * Generate OTP for the given payment entries.
	 *
	 * Note: Only single OTP is generated for all the payment entries.
	 *
	 * @param {string[]} payment_entries List of Payment Entry names
	 *
	 * ---
	 * Example Response:
	 * ```js
	 * {
	 * 	prompt: "Enter OTP sent to your mobile number.",
	 * 	method: "SMS",
	 * 	setup: true,
	 *  auth_id: "4896d98",
	 * }
	 * ```
	 */
	async generate_otp(payment_entries) {
		const response = await frappe.call(`${BASE_AUTH_PATH}.generate_otp`, {
			payment_entries,
		});

		return response?.message;
	},

	// ################ HELPERS ################ //
	/**
	 * Get authentication dialog details based on the verification method.
	 *
	 * @param {Object} generation_details  OTP generation details
	 * @returns {Object} Dialog details (title, fields)
	 */
	get_authentication_dialog_details(generation_details) {
		const { method, setup, prompt } = generation_details;

		const get_description = () => {
			if (setup) return __(prompt);

			return `<bold class='text-danger'>
						${__("There is some error! Please contact your Administrator.")}
					</bold>`;
		};

		// Base data for dialog fields
		const data = {
			title: __("Authenticate"),
			label: __("OTP"),
			fieldtype: "Data",
			description: get_description(),
		};

		// Update dialog details based on the verification method
		switch (method) {
			case this.AUTH_METHODS.OTP_APP:
				data.title = __("Authenticate using OTP App");
				break;
			case this.AUTH_METHODS.SMS:
				data.title = __("Authenticate using SMS");
				break;
			case this.AUTH_METHODS.EMAIL:
				data.title = __("Authenticate using Email");
				break;
			case this.AUTH_METHODS.PASSWORD:
				data.title = __("Authenticate using Password");
				data.label = __("Password");
				data.fieldtype = "Password";
				break;
		}

		return {
			title: data.title,
			fields: [
				{
					fieldname: "authenticator",
					reqd: 1,
					...data,
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
