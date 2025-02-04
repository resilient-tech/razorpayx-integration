// ############ CONSTANTS ############ //
const PE_BASE_PATH = "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry";

const PAYOUT_MODES = {
	BANK: "NEFT/RTGS",
	UPI: "UPI",
	LINK: "Link",
};

const PAYOUT_FIELDS = [
	// Common
	"payment_type",
	"bank_account",
	// Party
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
	// Integration
	"integration_doctype",
	"integration_docname",
	// Payout
	"paid_amount",
	"make_bank_online_payment",
	"razorpayx_payout_mode",
	"razorpayx_payout_desc",
	"razorpayx_payout_status",
	"razorpayx_pay_instantaneously",
	"razorpayx_payout_id",
	"razorpayx_payout_link_id",
	"reference_no",
];

const DESCRIPTION_REGEX = /^[a-zA-Z0-9 ]{1,30}$/;

frappe.ui.form.on("Payment Entry", {
	refresh: async function (frm) {
		// Do not allow to edit fields if Payment is processed by RazorpayX in amendment
		disable_payout_fields_in_amendment(frm);

		// permission checks
		const permission = user_has_payout_permissions(frm);
		toggle_payout_sections(frm, permission);

		if (frm.doc.integration_doctype !== razorpayx.RPX_DOCTYPE || !frm.doc.integration_docname) return;

		// payout is/will made via RazorpayX
		if (frm.doc.make_bank_online_payment) {
			set_razorpayx_state_description(frm);
			set_reference_no_description(frm);
		}

		if (!permission || is_already_paid(frm)) return;

		// user can make payout `on submit` or `after submit`
		update_submit_button_label(frm);

		// making payout manually
		if (frm.doc.docstatus === 1 && !frm.doc.make_bank_online_payment) {
			frm.add_custom_button(__("Make Payout"), () => show_make_payout_dialog(frm));
		}
	},

	validate: function (frm) {
		if (!razorpayx.is_payout_via_razorpayx(frm.doc)) return;

		if (frm.doc.razorpayx_pay_instantaneously && payment_utils.IMPS_LIMIT > frm.doc.paid_amount) {
			frm.set_value("razorpayx_pay_instantaneously", 0);
		}

		validate_payout_description(frm.doc.razorpayx_payout_desc);

		if (frm.doc.razorpayx_payout_mode === PAYOUT_MODES.LINK) {
			if (!frm.doc.contact_mobile && !frm.doc.contact_email) {
				let msg = "";

				if (frm.doc.party_type === "Employee") {
					msg = __("Set Employee's Mobile or Preferred Email to make payout with link.");
				} else {
					msg = __("Any one of Party's Mobile or Email is mandatory to make payout with link.");
				}

				frappe.throw({ message: msg, title: __("Contact Details Missing") });
			}
		}
	},

	party_bank_account: function (frm) {
		if (!frm.doc.party_bank_account) {
			frm.set_value("razorpayx_payout_mode", PAYOUT_MODES.LINK);
		}
	},

	before_submit: async function (frm) {
		if (
			!razorpayx.is_payout_via_razorpayx(frm.doc) ||
			is_already_paid(frm) ||
			!user_has_payout_permissions(frm)
		) {
			return;
		}

		frappe.validate = false;

		return new Promise((resolve) => {
			const continue_submission = (auth_id) => {
				frappe.validate = true;
				frm.__making_payout = true;

				payment_utils.set_onload(frm, "auth_id", auth_id);

				resolve();
			};

			return payment_utils.authenticate_payment_entries(frm.docname, continue_submission);
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
			!user_has_payout_permissions(frm) ||
			payment_utils.get_onload(frm, "auto_cancel_payout_enabled")
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

// ############ VALIDATIONS ############ //
function validate_payout_description(description) {
	if (!description || DESCRIPTION_REGEX.test(description)) return;

	frappe.throw({
		message: __(
			"Must be <strong>alphanumeric</strong> and contain <strong>spaces</strong> only, with a maximum of <strong>30</strong> characters."
		),
		title: __("Invalid RazorpayX Payout Description"),
	});
}

// ############ UTILITY ############ //
/**
 * If current Payment Entry is amended from another Payment Entry,
 * and original Payment Entry is processed (not mean by status) by RazorpayX, then disable
 * payout fields in the current Payment Entry.
 */
async function disable_payout_fields_in_amendment(frm) {
	if (!frm.doc.amended_from || frm.doc.docstatus == 2) return;

	let is_paid = is_already_paid(frm);

	if (is_paid === undefined) {
		const response = await frappe.db.get_value(
			"Payment Entry",
			frm.doc.amended_from,
			"make_bank_online_payment"
		);

		is_paid = response.message?.make_bank_online_payment || 0;
	}

	frm.toggle_enable(PAYOUT_FIELDS, is_paid ? 0 : 1);
}

function is_already_paid(frm) {
	return payment_utils.get_onload(frm, "is_already_paid");
}

function user_has_payout_permissions(frm) {
	if (frm.doc.__onload) {
		return payment_utils.get_onload(frm, "has_payout_permission");
	}

	return payment_utils.can_user_authorize_payout();
}

// ############ HELPERS ############ //
function update_submit_button_label(frm) {
	if (frm.doc.docstatus !== 0 || frm.doc.__islocal || !frm.doc.make_bank_online_payment) return;

	frm.page.set_primary_action(__("Pay and Submit"), () => {
		frm.savesubmit();
	});
}

function toggle_payout_sections(frm, permission) {
	const toggle = permission ? 1 : 0;

	frm.toggle_display("online_payment_section", toggle);
	frm.toggle_display("razorpayx_payout_section", toggle);
}

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

	const amended = payment_utils.get_onload(frm, "is_document_amended");
	const field = frm.get_field("payment_type");

	if (amended) {
		field.set_new_description(
			__("Check latest payout status here <strong>{0}</strong>", [
				frappe.utils.get_form_link("Payment Entry", amended, true),
			])
		);

		return;
	}
	const status = frm.doc.razorpayx_payout_status;

	// prettier-ignore
	// eslint-disable-next-line
	const description = `<div class="d-flex indicator ${get_indicator(status)} align-item-center justify-content-center">
							<strong>${status}</strong>
							${get_rpx_img_container("via")}
						</div>`;

	field.set_new_description(description);
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

	const not_processed = ["Not Initiated", "Queued", "Processing", "Pending", "Scheduled"];

	if (is_payout_link_cancelled() || not_processed.includes(frm.doc.razorpayx_payout_status)) return;

	frm.get_field("reference_no").set_new_description(
		__("This is <strong>UTR</strong> of the payout transaction done via <strong>RazorpayX</strong>")
	);
}

// ############ MAKING PAYOUT HELPERS ############ //
async function show_make_payout_dialog(frm) {
	// depends on conditions
	const BANK_MODE = `doc.razorpayx_payout_mode === '${PAYOUT_MODES.BANK}'`;
	const UPI_MODE = `doc.razorpayx_payout_mode === '${PAYOUT_MODES.UPI}'`;
	const LINK_MODE = `doc.razorpayx_payout_mode === '${PAYOUT_MODES.LINK}'`;

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
				fieldname: "razorpayx_payout_mode",
				label: __("Payout Mode"),
				fieldtype: "Select",
				options: Object.values(PAYOUT_MODES),
				default: frm.doc.razorpayx_payout_mode || PAYOUT_MODES.LINK,
				read_only: 1,
				reqd: 1,
				description: `<div class="d-flex align-items-center justify-content-end">
								${get_rpx_img_container("via")}
							</div>`,
			},
			{
				fieldname: "razorpayx_pay_instantaneously",
				label: "Pay Instantaneously",
				fieldtype: "Check",
				description: "Payment will be done with <strong>IMPS</strong> mode.",
				depends_on: `eval: ${BANK_MODE} && ${frm.doc.paid_amount <= payment_utils.IMPS_LIMIT}`,
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
		primary_action_label: __("{0} Pay", [frappe.utils.icon(payment_utils.PAY_ICON)]),
		primary_action: (values) => {
			validate_payout_description(values.razorpayx_payout_desc);

			dialog.hide();

			payment_utils.authenticate_payment_entries(frm.docname, async (auth_id) => {
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
			payout_mode: values.razorpayx_payout_mode,
			...values,
		},
		freeze: true,
		freeze_message: __("Making Payout ..."),
	});
}

async function set_party_bank_details(dialog) {
	const party_bank_account = dialog.get_value("party_bank_account");

	if (!party_bank_account) {
		dialog.set_value("razorpayx_payout_mode", PAYOUT_MODES.LINK);
		return;
	}

	const response = await frappe.db.get_value("Bank Account", party_bank_account, [
		"branch_code as party_bank_ifsc",
		"bank_account_no as party_bank_account_no",
		"upi_id as party_upi_id",
		"online_payment_mode as razorpayx_payout_mode",
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
