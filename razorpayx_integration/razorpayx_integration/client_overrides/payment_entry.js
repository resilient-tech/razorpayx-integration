// TODO: show it will pay by razorpayx

// TODO: Improve UX and UI for Payment Entry

// TODO: for UX: change submit button label to `Pay and Submit`

// ############ CONSTANTS ############ //
const BASE_API_PATH = "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry";

const PAYOUT_MODES = {
	BANK: "NEFT/RTGS",
	UPI: "UPI",
	LINK: "Link",
};

const PAYOUT_FIELDS = [
	//  Common
	"payment_type",
	"bank_account",
	// Party related
	"party",
	"party_type",
	"party_name",
	"party_bank_account",
	"party_bank_account_no",
	"party_bank_ifsc",
	"party_upi_id",
	"contact_person",
	"contact_mobile",
	"contact_email",
	// RazorpayX Related
	"paid_amount",
	"razorpayx_account",
	"make_bank_online_payment",
	"razorpayx_payout_mode",
	"razorpayx_payout_desc",
	"razorpayx_payout_status",
	"razorpayx_pay_instantaneously",
	"razorpayx_payout_id",
	"razorpayx_payout_link_id",
];

const RAZORPAYX_DOCTYPE = "RazorPayX Integration Setting";

// ############ DOC EVENTS ############ //
frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		// Do not allow to edit fields if Payment is processed by RazorpayX in amendment
		disable_payout_fields_in_amendment(frm);

		// TODO: permission check for showing the button
		if (
			!frm.doc.make_bank_online_payment &&
			frm.doc.docstatus === 1 &&
			frm.doc.payment_type === "Pay" &&
			frm.doc.mode_of_payment !== "Cash"
		) {
			frm.add_custom_button(__("{0} Make Payout", [frappe.utils.icon("expenses")]), () =>
				show_make_payout_dialog(frm)
			);
		}
	},

	validate: function (frm) {
		if (frm.doc.make_bank_online_payment && !frm.doc.reference_no) {
			frm.set_value("reference_no", "*** UTR WILL BE SET AUTOMATICALLY ***");
		}

		if (frm.doc.payment_type !== "Pay" || !frm.doc.razorpayx_account) {
			frm.set_value("make_bank_online_payment", 0);
		}

		reset_contact_details(frm);
	},

	bank_account: async function (frm) {
		if (!frm.doc.bank_account) {
			frm.set_value("razorpayx_account", "");
			frm.set_value("make_bank_online_payment", 0);
		} else {
			const account = await frappe.xcall(
				"razorpayx_integration.razorpayx_integration.utils.get_razorpayx_account_by_bank_account",
				{
					bank_account: frm.doc.bank_account,
				}
			);
			frm.set_value("razorpayx_account", account);
		}
	},

	party_bank_account: function (frm) {
		if (!frm.doc.party_bank_account) {
			frm.set_value("make_bank_online_payment", PAYOUT_MODES.LINK);
		}
	},

	contact_person: function (frm) {
		reset_contact_details(frm);
	},

	make_bank_online_payment: function (frm) {
		if (!frm.doc.make_bank_online_payment) return;

		if (!frm.doc.razorpayx_account) {
			frappe.show_alert({
				message: __("RazorpayX account not found. <br> Please set associate company's bank account."),
				indicator: "orange",
			});

			frm.set_value("make_bank_online_payment", 0);
		}
	},

	before_cancel: async function (frm) {
		if (
			!frm.doc.make_bank_online_payment ||
			!frm.doc.razorpayx_account ||
			!can_cancel_payout(frm) ||
			is_payout_already_cancelled(frm)
		) {
			return;
		}

		const auto_cancel_payout = await should_auto_cancel_payout(frm);
		if (auto_cancel_payout) return;

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

// ############ HELPERS ############ //
function reset_values(frm, ...fields) {
	fields.forEach((field) => frm.set_value(field, ""));
}

function reset_contact_details(frm) {
	if (!frm.doc.contact_person) {
		reset_values(frm, "contact_email", "contact_mobile");
	}
}

// ############ PE CANCEL HELPERS ############ //
/**
 * Check if the payout can be cancelled or not related to the Payment Entry.
 * @param {object} frm The doctype's form object
 * @returns {boolean} `true` if the payout can be cancelled, otherwise `false`
 */
function can_cancel_payout(frm) {
	return ["Not Initiated", "Queued"].includes(frm.doc.razorpayx_payout_status);
}

/**
 * Get the value of `auto_cancel_payout` field from RazorPayX Integration Setting
 * based on the selected RazorpayX Account.
 * @param {object} frm The doctype's form object
 * @returns {Promise<boolean>} The value of `auto_cancel_payout
 */
async function should_auto_cancel_payout(frm) {
	const auto_cancel = await frappe.xcall(`${BASE_API_PATH}.should_auto_cancel_payout`, {
		razorpayx_account: frm.doc.razorpayx_account,
	});

	return auto_cancel;
}

/**
 * Check if the payout is already cancelled or not.
 *
 * @returns {boolean} `true` if the payout is already cancelled, otherwise `false`
 */
function is_payout_already_cancelled(frm) {
	return ["Cancelled", "Failed", "Rejected", "Reversed"].includes(frm.doc.razorpayx_payout_status);
}

/**
 * Show dialog to confirm the cancellation of payout.
 *
 * Two options are available:
 * 1. Do not cancel the payout.
 * 2. Cancel the payout.
 *
 * @param {object} frm The doctype's form object
 * @param {function} callback The function to call after confirmation
 */
function show_cancel_payout_dialog(frm, callback) {
	const dialog = new frappe.ui.Dialog({
		title: __("Cancel Payment Entry with Payout"),
		fields: [
			{
				fieldname: "cancel_payout",
				label: __("Cancel Payout"),
				fieldtype: "Check",
				default: 1,
				description: __(
					"This will cancel the payout and payout link for this Payment Entry if checked."
				),
			},
		],
		primary_action_label: __("Continue"),
		primary_action: async (values) => {
			if (values.cancel_payout) {
				await frappe.call({
					method: `${BASE_API_PATH}.cancel_payout`,
					args: {
						doctype: frm.doctype,
						docname: frm.docname,
					},
				});

				frm.refresh();
			}

			callback && callback();
			dialog.hide();
		},
	});

	// Make primary action button Background Red
	dialog.get_primary_btn().removeClass("btn-primary").addClass("btn-danger");
	dialog.show();
}

// ############ MAKING PAYOUT HELPERS ############ //
async function show_make_payout_dialog(frm) {
	// depends on conditions
	const DEPENDS_ON_BANK = `doc.razorpayx_payout_mode === '${PAYOUT_MODES.BANK}'`;
	const DEPENDS_ON_UPI = `doc.razorpayx_payout_mode === '${PAYOUT_MODES.UPI}'`;
	const DEPENDS_ON_LINK = `doc.razorpayx_payout_mode === '${PAYOUT_MODES.LINK}'`;

	const dialog = new frappe.ui.Dialog({
		title: __("Enter Payout Details"),
		fields: [
			{
				fieldname: "account_section_break",
				label: __("Company Account Details"),
				fieldtype: "Section Break",
			},
			{
				fieldname: "bank_account",
				label: __("Company Bank Account"),
				fieldtype: "Link",
				options: "Bank Account",
				default: frm.doc.bank_account,
				reqd: 1,
				read_only: frm.doc.bank_account ? 1 : 0,
				get_query: function () {
					return {
						filters: {
							is_company_account: 1,
							company: frm.doc.company,
						},
					};
				},
			},
			{
				fieldname: "account_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "image_section",
				fieldtype: "HTML",
				options: `<img src="/assets/razorpayx_integration/images/RazorpayX-logo.png" />`,
			},
			{
				fieldname: "party_section_break",
				label: __("Party Details"),
				fieldtype: "Section Break",
			},
			{
				fieldname: "party_bank_account",
				label: __("Party Bank Account"),
				fieldtype: "Link",
				options: "Bank Account",
				default: frm.doc.party_bank_account,
				reqd: 1,
				read_only: frm.doc.party_bank_account ? 1 : 0,
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
					set_party_bank_details(dialog.get_value("party_bank_account"), dialog);
				},
			},
			{
				fieldname: "party_bank_account_no",
				label: "Party Bank Account No",
				fieldtype: "Data",
				read_only: 1,
				depends_on: `eval: ${DEPENDS_ON_BANK}`,
				mandatory_depends_on: `eval: ${DEPENDS_ON_BANK}`,
				default: frm.doc.party_bank_account_no,
			},
			{
				fieldname: "party_bank_ifsc",
				label: "Party Bank IFSC Code",
				fieldtype: "Data",
				read_only: 1,
				depends_on: `eval: ${DEPENDS_ON_BANK}`,
				mandatory_depends_on: `eval: ${DEPENDS_ON_BANK}`,
				default: frm.doc.party_bank_ifsc,
			},
			{
				fieldname: "party_upi_id",
				label: "Party UPI ID",
				fieldtype: "Data",
				read_only: 1,
				depends_on: `eval: ${DEPENDS_ON_UPI}`,
				mandatory_depends_on: `eval: ${DEPENDS_ON_UPI}`,
				default: frm.doc.party_upi_id,
			},
			{
				fieldname: "party_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "contact_person",
				label: __("Contact"),
				fieldtype: "Link",
				options: "Contact",
				default: frm.doc.contact_person,
				read_only: frm.doc.contact_person ? 1 : 0,
				depends_on: `eval: ${DEPENDS_ON_LINK}`,
				mandatory_depends_on: `eval: ${DEPENDS_ON_LINK}`,
				get_query: function () {
					return {
						filters: {
							link_doctype: frm.doc.party_type,
							link_name: frm.doc.party,
						},
					};
				},
				onchange: async function () {
					set_contact_details(dialog.get_value("contact_person"), dialog);
				},
			},
			{
				fieldname: "contact_email",
				label: "Email",
				fieldtype: "Data",
				options: "Email",
				depends_on: `eval: ${DEPENDS_ON_LINK} && doc.contact_person`,
				mandatory_depends_on: `eval: ${DEPENDS_ON_LINK}`,
				read_only: 1,
				default: frm.doc.contact_email,
			},
			{
				fieldname: "contact_mobile",
				label: "Mobile",
				fieldtype: "Data",
				options: "Phone",
				depends_on: `eval: ${DEPENDS_ON_LINK} && doc.contact_person`,
				read_only: 1,
				default: frm.doc.contact_mobile,
			},
			{
				fieldname: "payment_section_break",
				label: __("Payment Details"),
				fieldtype: "Section Break",
			},
			{
				fieldname: "razorpayx_payout_mode",
				label: __("Payout Mode"),
				fieldtype: "Select",
				options: Object.values(PAYOUT_MODES),
				reqd: 1,
			},
			{
				fieldname: "razorpayx_pay_instantaneously",
				label: "Pay Instantaneously",
				fieldtype: "Check",
				description: "Payment will be done with <strong>IMPS</strong> mode.",
				depends_on: `eval: ${DEPENDS_ON_BANK}`,
			},
			{
				fieldname: "party_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "razorpayx_payout_desc",
				label: __("Payout Description"),
				fieldtype: "Data",
				mandatory_depends_on: `eval: ${DEPENDS_ON_LINK}`,
			},
		],
		primary_action_label: __("Make Payout"),
		primary_action: (values) => {
			frappe.call({
				method: `${BASE_API_PATH}.make_payout_with_payment_entry`,
				args: {
					docname: frm.docname,
					...values,
				},
				freeze: true,
				freeze_message: __("Making Payout via RazorPayX..."),
				callback: (r) => {
					if (r.exc) return;

					frappe.show_alert({
						message: __("Payout has been made successfully."),
						indicator: "green",
					});
					frm.reload_doc();
				},
			});

			dialog.hide();
		},
	});

	set_default_payout_mode(frm.doc.party_bank_account, dialog);

	dialog.show();
}

async function set_default_payout_mode(party_bank_account, dialog) {
	if (!party_bank_account) return;

	const response = await frappe.db.get_value("Bank Account", party_bank_account, "online_payment_mode");

	dialog.set_value("razorpayx_payout_mode", response.message.online_payment_mode);
}

async function set_party_bank_details(party_bank_account, dialog) {
	if (!party_bank_account) return;

	const response = await frappe.db.get_value("Bank Account", party_bank_account, [
		"branch_code as party_bank_ifsc",
		"bank_account_no as party_bank_account_no",
		"upi_id as party_upi_id",
		"online_payment_mode as razorpayx_payout_mode",
	]);

	dialog.set_values(response.message);
}

async function set_contact_details(contact_person, dialog) {
	if (!contact_person) return;

	const response = await frappe.call({
		method: "frappe.contacts.doctype.contact.contact.get_contact_details",
		args: { contact: contact_person },
	});

	dialog.set_values({
		contact_email: response.message.contact_email,
		contact_mobile: response.message.contact_mobile,
	});
}

// ############ VALIDATIONS ############ //
/**
 * If current Payment Entry is amended from another Payment Entry,
 * and source Payment Entry is processed by RazorPayX, then disable
 * payout fields in the current Payment Entry.
 *
 * @param {object} frm The doctype's form object
 */
async function disable_payout_fields_in_amendment(frm) {
	if (!frm.doc.amended_from) return;

	let disable_payout_fields = frm.doc.__onload?.disable_payout_fields;

	if (disable_payout_fields === undefined) {
		const response = await frappe.db.get_value(
			"Payment Entry",
			frm.doc.amended_from,
			"make_bank_online_payment"
		);

		disable_payout_fields = response.message?.make_bank_online_payment || 0;
	}

	frm.toggle_enable(PAYOUT_FIELDS, disable_payout_fields ? 0 : 1);
}
