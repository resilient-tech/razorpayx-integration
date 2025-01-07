// TODO: update Party Bank Account filters
// TODO: show it will pay by razorpayx
// TODO: RazorpayX status fields also allow for edit after submit
// TODO: Backend validation for RazorpayX status fields !!!

// TODO: Update CF and CP for Payment Entry
// TODO: Work with new design for Payment Entry ???
// TODO: Improve UX and UI for Payment Entry

// TODO: for UX: change submit button label to `Pay and Submit`
// TODO: Button to create RazorpayX payout after submit if not paid by RazorpayX

const BASE_API_PATH = "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry";

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

frappe.ui.form.on("Payment Entry", {
	setup: function (frm) {
		frm.add_fetch("party_bank_account", "default_online_payment_mode", "razorpayx_payout_mode");
	},

	refresh: function (frm) {
		// Do not allow to edit fields if Payment is processed by RazorpayX in amendment
		disable_payout_fields_in_amendment(frm);

		// TODO: permission check for showing the button
		if (!frm.doc.make_bank_online_payment && frm.doc.docstatus === 1 && frm.doc.payment_type === "Pay") {
			frm.add_custom_button(__("Make Payout"), () => show_make_payout_dialog(frm));
		}
	},

	bank_account: async function (frm) {
		// TODO: when `make_online_payment` is checked, then fetch the RazorpayX Account otherwise no
		// and also when checking `make_online_payment` then fetch the RazorpayX Account if not set
		if (!frm.doc.bank_account) {
			frm.set_value("razorpayx_account", "");
		} else {
			const response = await frappe.db.get_value(
				"RazorPayX Integration Setting",
				{
					bank_account: frm.doc.bank_account,
				},
				"name"
			);

			const { name } = response.message || {};

			frm.set_value("razorpayx_account", name);
		}
	},

	contact_person: function (frm) {
		if (!frm.doc.contact_person) {
			frm.set_value("contact_mobile", "");
			frm.set_value("contact_email", "");
		}
	},

	before_cancel: async function (frm) {
		if (!frm.doc.make_bank_online_payment || is_payout_already_cancelled(frm)) return;

		// Check Payout is cancellable or not
		if (!can_cancel_payout(frm)) {
			frappe.throw({
				message: __(
					"Payment Entry cannot be cancelled as Payout is already in <strong>{0}</strong> state.",
					[frm.doc.razorpayx_payout_status]
				),
				title: __("Cannot Cancel Payment Entry"),
			});
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

/**
 * Check if the payout can be cancelled or not related to the Payment Entry.
 * @param {object} frm The doctype's form object
 * @returns {boolean} `true` if the payout can be cancelled, otherwise `false`
 */
function can_cancel_payout(frm) {
	return (
		frm.doc.make_bank_online_payment &&
		["Not Initiated", "Queued"].includes(frm.doc.razorpayx_payout_status)
	);
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
					method: `${BASE_API_PATH}.cancel_payout_and_payout_link`,
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

async function show_make_payout_dialog(frm) {
	const payout_modes = await frappe.xcall(`${BASE_API_PATH}.get_user_payout_modes`);

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
					set_default_payout_mode(dialog.get_value("party_bank_account"), dialog);
				},
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
				get_query: function () {
					return {
						filters: {
							link_doctype: frm.doc.party_type,
							link_name: frm.doc.party,
						},
					};
				},
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
				options: payout_modes,
				reqd: 1,
				onchange: function () {
					const payout_mode = dialog.get_value("razorpayx_payout_mode");

					if (payout_mode === "NEFT/RTGS") {
						toggle_dialog_fields(dialog, 0, "razorpayx_pay_instantaneously");
						toggle_dialog_fields(dialog, 1, "contact_person");
						toggle_required(dialog, 0, "razorpayx_payout_desc", "contact_person");
					} else if (payout_mode === "UPI") {
						toggle_dialog_fields(dialog, 1, "razorpayx_pay_instantaneously", "contact_person");
						toggle_required(dialog, 0, "razorpayx_payout_desc", "contact_person");
					} else {
						toggle_dialog_fields(dialog, 0, "contact_person");
						toggle_required(dialog, 1, "razorpayx_payout_desc", "contact_person");
					}
				},
			},
			{
				fieldname: "razorpayx_pay_instantaneously",
				label: "Pay Instantaneously",
				fieldtype: "Check",
				description: "Payment will be done with <strong>IMPS</strong> mode.",
				hidden: 1,
			},
			{
				fieldname: "party_cb",
				fieldtype: "Column Break",
			},
			{
				fieldname: "razorpayx_payout_desc",
				label: __("Payout Description"),
				fieldtype: "Data",
			},
		],
		primary_action_label: __("Make Payout"),
		primary_action: async (values) => {
			dialog.hide();
		},
	});

	set_default_payout_mode(frm.doc.party_bank_account, dialog);
	dialog.show();
}

async function set_default_payout_mode(party_bank_account, dialog) {
	if (!party_bank_account) return;

	const response = await frappe.db.get_value(
		"Bank Account",
		party_bank_account,
		"default_online_payment_mode"
	);
	dialog.set_value("razorpayx_payout_mode", response.message.default_online_payment_mode);
}

function toggle_dialog_fields(dialog, hide, ...fields) {
	fields.forEach((field) => {
		dialog.set_df_property(field, "hidden", hide);
	});
}

function toggle_required(dialog, required, ...fields) {
	fields.forEach((field) => {
		dialog.set_df_property(field, "reqd", required);
	});
}
