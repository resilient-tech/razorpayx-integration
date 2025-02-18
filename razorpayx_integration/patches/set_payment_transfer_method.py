import frappe
from payment_integration_utils.payment_integration_utils.constants.payments import (
    TRANSFER_METHOD,
)


def execute():
    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={"make_bank_online_payment": 1},
        fields=[
            "name",
            "razorpayx_payout_mode",
            "razorpayx_pay_instantaneously",
            "paid_amount",
        ],
    )

    if not payment_entries:
        return

    updated_payment_entries = {}

    for payment_entry in payment_entries:
        if payment_entry.razorpayx_payout_mode in [
            TRANSFER_METHOD.LINK.value,
            TRANSFER_METHOD.UPI.value,
        ]:
            transfer_method = payment_entry.razorpayx_payout_mode
        elif payment_entry.razorpayx_pay_instantaneously:
            transfer_method = TRANSFER_METHOD.IMPS.value
        elif payment_entry.paid_amount > 2_00_000:
            transfer_method = TRANSFER_METHOD.RTGS.value
        else:
            transfer_method = TRANSFER_METHOD.NEFT.value

        updated_payment_entries[payment_entry.name] = {
            "payment_transfer_method": transfer_method,
        }

    if updated_payment_entries:
        frappe.db.bulk_update("Payment Entry", updated_payment_entries)
