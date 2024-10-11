// todo : different events for validation (Ref: https://github.com/resilient-tech/bank_integration/blob/edb06993e9257d6cfbc377242f3ef9051dc9fd50/bank_integration/scripts/payment_entry.js )

frappe.ui.form.on("Payment Entry", {
	setup: function (frm) {
		frm.set_query("party_type", function () {
			return {
				filters: {
					name: ["in", ["Employee", "Customer", "Supplier"]],
				},
			};
		});

		frm.add_fetch("party_bank_acc", "bank", "party_bank");
		frm.add_fetch("party_bank_acc", "bank_account_no", "party_bank_ac_no");
		frm.add_fetch("party_bank_acc", "branch_code", "party_bank_branch_code");
	},

	onload: function (frm) {
		// todo: need to understand the use case
		$('input[data-fieldname="payment_desc"]').keypress(function (e) {
			var regex = new RegExp("^[a-zA-Z0-9 ]+$");
			var str = String.fromCharCode(!e.charCode ? e.which : e.charCode);
			if (regex.test(str)) {
				return true;
			}

			e.preventDefault();
			return false;
		});
	},

	refresh: function (frm) {
		if (frm.doc.docstatus === 0) {
			frm.fields_dict.payment_desc.$input[0].maxLength = 20;
		}

		if (
			frm.doc.docstatus != 0 ||
			frm.doc.__unsaved ||
			!frm.doc.pay_now ||
			frm.doc.razorpayx_payment_status === "Not Initiated"
		)
			return;

		// Add RazorpayX Payment Button
		frm.add_custom_button(__("Make Online Payment"), () => make_online_payment(frm));
	},

	validate: function (frm) {
		if (frm.doc.docstatus === 0 && frm.doc.paid_from && frm.doc.pay_now && !frm.doc.razorpayx_account) {
			frappe.throw(__("Not Found Associate RazorpayX Account for Paid From Account"));
		}

		if (frm.doc.docstatus === 0 && frm.get_docfield("pay_now").hidden_due_to_dependency) {
			frm.set_value("pay_now", 0);
		}
	},

	after_save: function (frm) {
		if (frm.docstatus == 0 && frm.doc.pay_on_submit) {
			frappe.show_alert({
				message: __("Payment will be made on submit automatically"),
				indicator: "blue",
			});
		}
	},

	payment_type: function (frm) {
		check_razorpayx_integration(frm);
	},

	// ! BUG: it is called twice when we changes, so caused twice API call
	paid_from: function (frm) {
		check_razorpayx_integration(frm);
	},

	party: function (frm) {
		set_party_bank_account(frm);
	},

	pay_now: function (frm) {
		if (frm.doc.payment_type !== "pay") return;

		if (!frm.doc.razorpayx_account) {
			check_razorpayx_integration(frm);
		}

		set_party_bank_account(frm);

		if (frm.doc.pay_now) {
			// set reference details
			frm.set_value("reference_no", "-");
			frm.set_value("reference_date", frappe.datetime.get_today());
		} else {
			reset_fields(frm, "reference_no", "reference_date");
		}
	},

	payment_desc: function (frm) {
		frm.set_value("payment_desc", frm.doc.payment_desc.replace(/[^a-zA-Z0-9 ]/gi, ""));
	},
});

async function check_razorpayx_integration(frm) {
	if (frm.doc.payment_type !== "Pay" || !frm.doc.paid_from) return;

	// get associate razorpayx integration account
	const response = await frappe.call("razorpayx_integration.utils.get_associate_razorpayx_account", {
		paid_from_account: frm.doc.paid_from,
		fieldname: ["name", "disabled", "pay_on_submit"],
	});

	if (response.message) {
		const { name, disabled, pay_on_submit } = response.message;

		frm.set_value("razorpayx_account", name);
		frm.set_value("pay_on_submit", pay_on_submit);

		if (disabled) {
			disable_pay_now(frm);
		} else {
			frm.get_docfield("pay_now").read_only = 0;
			frm.refresh_field("pay_now");
		}
	} else {
		reset_fields(frm, "razorpayx_account");
		disable_pay_now(frm);
	}
}

function disable_pay_now(frm) {
	frm.set_value("pay_now", 0);
	frm.get_docfield("pay_now").read_only = 1;
	frm.refresh_field("pay_now");
}

function reset_fields(frm, ...fields) {
	for (const field of fields) {
		frm.set_value(field, "");
	}
}

async function set_party_bank_account(frm) {
	if (!frm.doc.pay_now || !frm.doc.party_type || !frm.doc.party) return;

	const response = await frappe.db.get_value(frm.doc.party_type, { name: frm.doc.party }, "bank_account");

	if (response.message?.bank_account) {
		frm.set_value("party_bank_acc", response.message.bank_account);
	}
}

function make_online_payment(frm) {}
