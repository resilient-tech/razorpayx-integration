import frappe

from razorpayx_integration.constants import RAZORPAYX_CONFIG


def execute():
    frappe.db.set_value(
        "Payment Entry",
        {
            "integration_doctype": "RazorpayX Integration Setting",
        },
        "integration_doctype",
        RAZORPAYX_CONFIG,
    )
