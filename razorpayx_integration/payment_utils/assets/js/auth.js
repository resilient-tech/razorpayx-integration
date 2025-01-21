frappe.provide("payment_utils");

const AUTH_METHODS = {
	OTP_APP: "OTP App",
	SMS: "SMS",
	EMAIL: "Email",
	PASSWORD: "Password",
};

const BASE_AUTH_PATH = "razorpayx_integration.payment_utils.auth";

Object.assign(payment_utils, {
	// ################ CONSTANTS ################ //
	AUTH_METHODS,

	// ################ UTILITIES ################ //
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
	async authenticate_payment_entries(payment_entries, callback) {
		if (typeof payment_entries === "string") {
			payment_entries = [payment_entries];
		}

		const generation_details = await this.generate_otp(payment_entries);
		if (!generation_details) return;

		const { title, fields } = this.get_authentication_dialog_details(generation_details);

		const dialog = new frappe.ui.Dialog({
			title: title,
			fields: fields,
			primary_action_label: __("{0} Authenticate", [frappe.utils.icon("permission")]),
			primary_action: async (values) => {
				const { verified, message } = await this.verify_otp(
					values.authenticator,
					generation_details.auth_id,
					generation_details.method === AUTH_METHODS.PASSWORD
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

		if (generation_details.method === AUTH_METHODS.PASSWORD) {
			dialog.get_field("authenticator").disable_password_checks();
		}

		dialog.get_field("authenticator").set_focus();
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
		const response = await frappe.call({
			method: `${BASE_AUTH_PATH}.generate_otp`,
			args: {
				payment_entries,
			},
			freeze: true,
			freeze_message: __("Please wait for authentication..."),
		});

		return response?.message;
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
	 * 	message: "OTP verified successfully.",
	 * }
	 * ```
	 */
	async verify_otp(authenticator, auth_id, is_password = false) {
		const get_freeze_message = () => (is_password ? __("Verifying Password...") : __("Verifying OTP..."));

		const response = await frappe.call({
			method: `${BASE_AUTH_PATH}.verify_otp`,
			args: {
				otp: authenticator,
				auth_id: auth_id,
			},
			freeze: true,
			freeze_message: get_freeze_message(),
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

			return `<bold class='text-danger font-weight-bold'>
						${frappe.utils.icon("solid-error")} &nbsp;
						${__("There is some error! Please contact your Administrator.")}
					</bold>`;
		};

		let dialog_title = __("Authenticate");

		const auth_field = {
			fieldname: "authenticator",
			label: __("OTP"),
			fieldtype: "Data",
			description: get_description(),
			reqd: 1,
		};

		// Update dialog details based on the verification method
		switch (method) {
			case AUTH_METHODS.OTP_APP:
				dialog_title = __("Authenticate using OTP App");
				break;
			case AUTH_METHODS.SMS:
				dialog_title = __("Authenticate using SMS");
				break;
			case AUTH_METHODS.EMAIL:
				dialog_title = __("Authenticate using Email");
				break;
			case AUTH_METHODS.PASSWORD:
				dialog_title = __("Authenticate using Password");
				auth_field.label = __("Password");
				auth_field.fieldtype = "Password";
				break;
		}

		return {
			title: dialog_title,
			fields: [
				{
					fieldname: "info",
					fieldtype: "HTML",
					options: `<div class="form-message yellow">
								<div>${__("Do not close this dialog until you authenticate.")}</div>
							</div>`,
				},
				auth_field,
			],
		};
	},
});
