import frappe

from razorpayx_integration.constants import PAYMENTS_PROCESSOR_APP, RAZORPAYX_CONFIG


def execute():
    if PAYMENTS_PROCESSOR_APP in frappe.get_installed_apps():
        return

    frappe.db.set_value(RAZORPAYX_CONFIG, {}, "pay_on_auto_submit", 0)
