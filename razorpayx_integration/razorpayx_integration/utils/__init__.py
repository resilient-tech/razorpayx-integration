import json

import frappe
from frappe import _

from razorpayx_integration.razorpayx_integration.constants import (
    RAZORPAYX_SETTING_DOCTYPE,
)


@frappe.whitelist()
def get_associate_razorpayx_account(
    paid_from_account: str, fieldname: list | str | None = None
) -> dict | None:
    frappe.has_permission(RAZORPAYX_SETTING_DOCTYPE)

    if not fieldname:
        fieldname = "name"
    elif isinstance(fieldname, str):
        fieldname = json.loads(fieldname)

    bank_account = frappe.db.get_value(
        "Bank Account", {"account": paid_from_account}, "name"
    )

    if not bank_account:
        return

    return frappe.db.get_value(
        RAZORPAYX_SETTING_DOCTYPE,
        {"bank_account": bank_account},
        fieldname,
        as_dict=True,
    )


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_SETTING_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )
