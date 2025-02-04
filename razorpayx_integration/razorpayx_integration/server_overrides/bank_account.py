import frappe
from erpnext.accounts.doctype.bank_account.bank_account import BankAccount
from frappe import _

from razorpayx_integration.razorpayx_integration.constants.payouts import (
    USER_PAYOUT_MODE,
)


def validate(doc: BankAccount, method=None):
    if doc.is_company_account or not doc.party_type or not doc.party:
        return

    if doc.online_payment_mode == USER_PAYOUT_MODE.BANK.value:
        if not doc.branch_code:
            frappe.throw(
                msg=_(
                    "Branch Code (IFSC) is mandatory for <strong>{0}</strong> mode"
                ).format(USER_PAYOUT_MODE.BANK.value),
                title=_("Branch Code Missing"),
            )

        if not doc.bank_account_no:
            frappe.throw(
                msg=_(
                    "Bank Account Number is mandatory for <strong>{0}</strong> mode"
                ).format(USER_PAYOUT_MODE.BANK.value),
                title=_("Bank Account Number Missing"),
            )

    if doc.online_payment_mode == USER_PAYOUT_MODE.UPI.value:
        if not doc.upi_id:
            frappe.throw(
                msg=_("UPI ID is mandatory for <strong>{0}</strong> mode").format(
                    USER_PAYOUT_MODE.UPI.value
                ),
                title=_("UPI ID Missing"),
            )
