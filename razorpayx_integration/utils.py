import frappe

from razorpayx_integration.constant import RAZORPAYX_SETTING_DOCTYPE


def get_razorpayx_account(account_name: str):
    return frappe.get_doc(RAZORPAYX_SETTING_DOCTYPE, account_name)
