import frappe

from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_MODE,
)


def execute():
    """
    Set default `RazorpayX` payment mode in existing `Bank Account` records
    """

    BA = frappe.qb.DocType("Bank Account")

    (
        frappe.qb.update(BA)
        .set("payment_mode", RAZORPAYX_PAYOUT_MODE.BANK.value)
        .where(BA.is_company_account == 0)
        .where(BA.payment_mode.isnull())
        .run()
    )
