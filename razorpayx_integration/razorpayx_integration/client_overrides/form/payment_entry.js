// ############ CONSTANTS ############ //
const PE_BASE_PATH = "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry";

const TRANSFER_METHOD = payment_integration_utils.PAYMENT_TRANSFER_METHOD;

frappe.ui.form.on("Payment Entry", {
	refresh: async function (frm) {
		// permission checks
		const permission = has_payout_permissions(frm);
		frm.toggle_display("razorpayx_payout_section", permission);

		if (frm.doc.integration_doctype !== razorpayx.RPX_DOCTYPE || !frm.doc.integration_docname) return;

		// payout is/will made via RazorpayX
		if (frm.doc.make_bank_online_payment) {
			set_razorpayx_state_description(frm);
			set_reference_no_description(frm);
		}

		if (!permission || is_already_paid(frm)) return;

		// making payout manually
		if (frm.doc.docstatus === 1 && !frm.doc.make_bank_online_payment) {
			frm.add_custom_button(__("Make Payout"), () => show_make_payout_dialog(frm));
		}
	},

	validate: function (frm) {
		if (!razorpayx.is_payout_via_razorpayx(frm.doc)) return;

		razorpayx.validate_payout_description(frm.doc.razorpayx_payout_desc);
	},

	before_submit: async function (frm) {
		if (
			!razorpayx.is_payout_via_razorpayx(frm.doc) ||
			is_already_paid(frm) ||
			!has_payout_permissions(frm)
		) {
			return;
		}

		frappe.validate = false;

		return new Promise((resolve) => {
			const continue_submission = (auth_id) => {
				frappe.validate = true;
				frm.__making_payout = true;

				payment_integration_utils.set_onload(frm, "auth_id", auth_id);

				resolve();
			};

			return payment_integration_utils.authenticate_payment_entries(frm.docname, continue_submission);
		});
	},

	on_submit: function (frm) {
		if (!frm.__making_payout) return;

		frappe.show_alert({
			message: __("Payout has been made successfully."),
			indicator: "green",
		});

		delete frm.__making_payout;
	},

	before_cancel: async function (frm) {
		if (
			!razorpayx.is_payout_via_razorpayx(frm.doc) ||
			!can_cancel_payout(frm) ||
			!has_payout_permissions(frm) ||
			payment_integration_utils.get_onload(frm, "auto_cancel_payout_enabled")
		) {
			return;
		}

		frappe.validate = false;

		return new Promise((resolve) => {
			const continue_cancellation = () => {
				frappe.validate = true;
				resolve();
			};

			return show_cancel_payout_dialog(frm, continue_cancellation);
		});
	},
});

function is_already_paid(frm) {
	return payment_integration_utils.is_already_paid(frm);
}

function has_payout_permissions(frm) {
	return payment_integration_utils.user_has_payment_permissions(frm);
}

// ############ HELPERS ############ //

function get_indicator(status) {
	const indicator = {
		"Not Initiated": "cyan",
		Queued: "yellow",
		Pending: "yellow",
		Scheduled: "purple",
		Processing: "blue",
		Processed: "green",
		Failed: "red",
		Cancelled: "red",
		Rejected: "red",
		Reversed: "red",
	};

	return indicator[status] || "grey";
}

function get_rpx_img_container(txt, styles = "", classes = "") {
	return `<div style="height: 25px; margin-left: auto; ${styles}" class="d-flex align-items-center ${classes}">
			<span>${__(txt)}</span> &nbsp;
			<img src="/assets/razorpayx_integration/images/razorpayx-logo.png" class="img-fluid" style="height: 100%; width: auto;" />
		</div>`;
}

function set_razorpayx_state_description(frm) {
	if (frm.doc.__islocal) return;

	const status = frm.doc.razorpayx_payout_status;

	// prettier-ignore
	// eslint-disable-next-line
	const description = `<div class="d-flex indicator ${get_indicator(status)} align-item-center justify-content-center">
							<strong>${status}</strong>
							${get_rpx_img_container("via")}
						</div>`;

	frm.get_field("payment_type").set_new_description(description);
}

function set_reference_no_description(frm) {
	// only payout link available and got cancelled
	function is_payout_link_cancelled() {
		return (
			frm.doc.razorpayx_payout_link_id &&
			!frm.doc.razorpayx_payout_id &&
			frm.doc.razorpayx_payout_status === "Cancelled"
		);
	}

	if (!["Reversed", "Processed"].includes(frm.doc.razorpayx_payout_status) || is_payout_link_cancelled())
		return;

	frm.get_field("reference_no").set_new_description(
		__("This is <strong>UTR</strong> of the payout transaction done via <strong>RazorpayX</strong>")
	);
}

// ############ MAKING PAYOUT HELPERS ############ //
async function show_make_payout_dialog(frm) {
	if (frm.is_dirty()) {
		frappe.throw({
			message: __("Please save the document's changes before making payout."),
			title: __("Unsaved Changes"),
		});
	}

	// depends on conditions
	const BANK_MODE = `["${TRANSFER_METHOD.NEFT}", "${TRANSFER_METHOD.RTGS}", "${TRANSFER_METHOD.IMPS}"].includes(doc.payment_transfer_method)`;
	const UPI_MODE = `doc.payment_transfer_method === '${TRANSFER_METHOD.UPI}'`;
	const LINK_MODE = `doc.payment_transfer_method === '${TRANSFER_METHOD.LINK}'`;

	const dialog = new frappe.ui.Dialog({
		title: __("Enter Payout Details"),
		fields: [
			{
				fieldname: "party_account_sec_break",
				label: __("Party Account Details"),
				fieldtype: "Section Break",
			},
			{
				fieldname: "party_bank_account",
				label: __("Party Bank Account"),
				fieldtype: "Link",
				options: "Bank Account",
				default: frm.doc.party_bank_account,
				get_query: function () {
					return {
						filters: {
							is_company_account: 0,
							party: frm.doc.party,
							party_type: frm.doc.party_type,
						},
					};
				},
				onchange: async function () {
					set_party_bank_details(dialog);
				},
			},
			{
				fieldname: "party_acc_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "party_bank_account_no",
				label: "Party Bank Account No",
				fieldtype: "Data",
				read_only: 1,
				depends_on: `eval: ${BANK_MODE}`,
				mandatory_depends_on: `eval: ${BANK_MODE}`,
				default: frm.doc.party_bank_account_no,
			},
			{
				fieldname: "party_bank_ifsc",
				label: "Party Bank IFSC Code",
				fieldtype: "Data",
				read_only: 1,
				depends_on: `eval: ${BANK_MODE}`,
				mandatory_depends_on: `eval: ${BANK_MODE}`,
				default: frm.doc.party_bank_ifsc,
			},
			{
				fieldname: "party_upi_id",
				label: "Party UPI ID",
				fieldtype: "Data",
				read_only: 1,
				depends_on: `eval: ${UPI_MODE}`,
				mandatory_depends_on: `eval: ${UPI_MODE}`,
				default: frm.doc.party_upi_id,
			},
			{
				fieldname: "party_contact_sec_break",
				label: __("Party Contact Details"),
				fieldtype: "Section Break",
			},
			{
				fieldname: "contact_person",
				label: __("Contact"),
				fieldtype: "Link",
				options: "Contact",
				default: frm.doc.contact_person,
				mandatory_depends_on: `eval: ${LINK_MODE} && ${frm.doc.party_type !== "Employee"}`,
				get_query: function () {
					return {
						filters: {
							link_doctype: frm.doc.party_type,
							link_name: frm.doc.party,
						},
					};
				},
				onchange: async function () {
					set_contact_details(dialog);
				},
			},
			{
				fieldname: "contact_email",
				label: "Email",
				fieldtype: "Data",
				options: "Email",
				// depends_on: "eval: doc.contact_email",
				read_only: 1,
				default: frm.doc.contact_email,
			},
			{
				fieldname: "party_contact_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "contact_mobile",
				label: "Mobile",
				fieldtype: "Data",
				options: "Phone",
				depends_on: "eval: doc.contact_mobile",
				read_only: 1,
				default: frm.doc.contact_mobile,
			},

			{
				fieldname: "payout_section_break",
				label: __("Payout Details"),
				fieldtype: "Section Break",
			},
			{
				fieldname: "payment_transfer_method",
				label: __("Payout Transfer Method"),
				fieldtype: "Select",
				options: Object.values(TRANSFER_METHOD),
				default: frm.doc.payment_transfer_method,
				reqd: 1,
				description: `<div class="d-flex align-items-center justify-content-end">
								${get_rpx_img_container("via")}
							</div>`,
			},
			{
				fieldname: "payout_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "razorpayx_payout_desc",
				label: __("Payout Description"),
				fieldtype: "Data",
				length: 30,
				mandatory_depends_on: `eval: ${LINK_MODE}`,
			},
		],
		primary_action_label: __("{0} Pay", [frappe.utils.icon(payment_integration_utils.PAY_ICON)]),
		primary_action: (values) => {
			razorpayx.validate_payout_description(values.razorpayx_payout_desc);
			payment_integration_utils.validate_payment_transfer_method(
				values.payment_transfer_method,
				frm.doc.paid_amount
			);

			dialog.hide();

			payment_integration_utils.authenticate_payment_entries(frm.docname, async (auth_id) => {
				await make_payout(auth_id, frm.docname, values);

				frappe.show_alert({
					message: __("Payout has been made successfully."),
					indicator: "green",
				});
			});
		},
	});

	dialog.show();
}

function make_payout(auth_id, docname, values) {
	return frappe.call({
		method: `${PE_BASE_PATH}.make_payout_with_razorpayx`,
		args: {
			auth_id: auth_id,
			docname: docname,
			transfer_method: values.payment_transfer_method,
			...values,
		},
		freeze: true,
		freeze_message: __("Making Payout ..."),
	});
}

async function set_party_bank_details(dialog) {
	const party_bank_account = dialog.get_value("party_bank_account");

	if (!party_bank_account) {
		dialog.set_value("payment_transfer_method", TRANSFER_METHOD.LINK);
		return;
	}

	dialog.set_value("payment_transfer_method", TRANSFER_METHOD.NEFT);

	const response = await frappe.db.get_value("Bank Account", party_bank_account, [
		"branch_code as party_bank_ifsc",
		"bank_account_no as party_bank_account_no",
		"upi_id as party_upi_id",
	]);

	dialog.set_values(response.message);
}

async function set_contact_details(dialog) {
	const contact_person = dialog.get_value("contact_person");

	if (!contact_person) {
		dialog.set_values({
			contact_email: "",
			contact_mobile: "",
		});
		return;
	}

	const response = await frappe.call({
		method: "frappe.contacts.doctype.contact.contact.get_contact_details",
		args: { contact: contact_person },
	});

	dialog.set_values({
		contact_email: response.message.contact_email,
		contact_mobile: response.message.contact_mobile,
	});
}

// ############ CANCELING PAYOUT HELPERS ############ //
function can_cancel_payout(frm) {
	return ["Not Initiated", "Queued"].includes(frm.doc.razorpayx_payout_status);
}

function show_cancel_payout_dialog(frm, callback) {
	const dialog = new frappe.ui.Dialog({
		title: __("Cancel Payout"),
		fields: [
			{
				fieldname: "cancel_payout",
				label: __("Cancel Payout"),
				fieldtype: "Check",
				default: 1,
				description: __("Payout will be cancelled along with Payment Entry if checked."),
			},
		],
		primary_action_label: __("Continue"),
		primary_action: (values) => {
			dialog.hide();

			frappe.call({
				method: `${PE_BASE_PATH}.mark_payout_for_cancellation`,
				args: {
					docname: frm.docname,
					cancel: values.cancel_payout,
				},
			});

			callback && callback();
		},
	});

	// Make primary action button Background Red
	dialog.get_primary_btn().removeClass("btn-primary").addClass("btn-danger");
	dialog.show();
}
