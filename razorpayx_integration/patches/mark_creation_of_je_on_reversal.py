import frappe

from razorpayx_integration.constants import RAZORPAYX_CONFIG


def execute():
    frappe.db.set_value(RAZORPAYX_CONFIG, {}, "create_je_on_reversal", 1)
