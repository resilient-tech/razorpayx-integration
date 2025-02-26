import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

from razorpayx_integration.constants import RAZORPAYX_SETTING


def is_payout_via_razorpayx(doc: PaymentEntry) -> bool:
    """
    Check if the Payment Entry is paid via RazorpayX.
    """
    return bool(
        doc.make_bank_online_payment
        and doc.integration_doctype == RAZORPAYX_SETTING
        and doc.integration_docname
    )


def is_auto_cancel_payout_enabled(razorpayx_setting: str) -> bool | int:
    return frappe.db.get_value(
        RAZORPAYX_SETTING, razorpayx_setting, "auto_cancel_payout"
    )


def is_auto_pay_enabled(razorpayx_setting: str) -> bool | int:
    return frappe.db.get_value(
        RAZORPAYX_SETTING, razorpayx_setting, "pay_on_auto_submit"
    )


def get_fees_accounting_config(razorpayx_setting: str) -> dict:
    return (
        frappe.db.get_value(
            RAZORPAYX_SETTING,
            razorpayx_setting,
            [
                "automate_fees_accounting",
                "creditors_account",
                "creditor_party",
                "payable_account",
            ],
        )
        or frappe._dict()
    )
