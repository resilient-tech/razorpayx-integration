import json

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE


@frappe.whitelist()
def get_razorpayx_account(company_bank_account: str) -> str | None:
    frappe.has_permission(RAZORPAYX_INTEGRATION_DOCTYPE, throw=True)

    return frappe.db.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        {"bank_account": company_bank_account},
        "name",
    )


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )
