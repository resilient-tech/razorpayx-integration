import frappe

from razorpayx_integration.constants import RAZORPAYX_CONFIG
from razorpayx_integration.razorpayx_integration.constants.payouts import PAYOUT_FROM


def execute():
    frappe.db.set_value(
        RAZORPAYX_CONFIG, {}, "payouts_from", PAYOUT_FROM.CURRENT_ACCOUNT.value
    )
