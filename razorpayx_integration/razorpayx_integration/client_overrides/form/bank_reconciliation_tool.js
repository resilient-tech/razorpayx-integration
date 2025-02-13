// Copyright (c) 2025, Resilient Tech and contributors
// For license information, please see license.txt
const SYNC_BTN_LABEL = __("Sync via RazorpayX");

frappe.ui.form.on("Bank Reconciliation Tool", {
	refresh: async function (frm) {
		frm.add_custom_button(SYNC_BTN_LABEL, async () => {
			await sync_transactions(frm.doc.bank_account, frm.__razorpayx_setting);

			frappe.show_alert({
				message: __("<strong>{0}</strong> transactions synced successfully!", [frm.doc.bank_account]),
				indicator: "green",
			});
		});

		await toggle_sync_btn(frm);
	},

	bank_account: async function (frm) {
		await toggle_sync_btn(frm);
	},
});

function sync_transactions(bank_account, razorpayx_setting) {
	return frappe.call({
		method: "razorpayx_integration.razorpayx_integration.utils.bank_transaction.sync_transactions_for_reconcile",
		args: { bank_account, razorpayx_setting },
		freeze: true,
		freeze_message: __("Syncing Transactions. Please wait it may take a while..."),
	});
}

async function toggle_sync_btn(frm) {
	const btn = frm.custom_buttons[SYNC_BTN_LABEL];

	if (!btn) return;

	if (!frm.doc.bank_account) {
		btn.hide();
		return;
	}

	const { name } = await razorpayx.get_razorpayx_setting(frm.doc.bank_account);
	frm.__razorpayx_setting = name;

	if (name) btn.show();
	else btn.hide();
}
