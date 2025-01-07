import frappe

from razorpayx_integration.razorpayx_integration.constants.payouts import (
    USER_PAYOUT_MODE,
)


def execute():
    """
    Approve existing `Bank Account` records.
    """

    BA = frappe.qb.DocType("Bank Account")

    (
        frappe.qb.update(BA)
        .set(BA.default_online_payment_mode, USER_PAYOUT_MODE.BANK.value)
        .where(BA.default_online_payment_mode.isnull())
        .run()
    )
