import frappe

from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_MODE,
)


def execute():
    """
    Approve existing `Bank Account` records.
    """

    BA = frappe.qb.DocType("Bank Account")

    (
        frappe.qb.update(BA)
        .set(BA.online_payment_mode, RAZORPAYX_PAYOUT_MODE.BANK.value)
        .where(BA.online_payment_mode.isnull())
        .run()
    )
