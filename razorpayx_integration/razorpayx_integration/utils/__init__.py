from typing import Literal

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_SETTING


@frappe.request_cache
def get_razorpayx_setting(
    identifier: str,
    search_by: Literal["bank_account", "account_id"],
    fields: list[str] | None = None,
    as_dict: bool = True,
) -> dict:
    """
    Fetch the RazorpayX Integration Setting name based on the identifier.

    :param identifier: The identifier to search by.
    :param search_by: Field to search by.
    :param fields: Fields to fetch.
    :param as_dict: Return as dict or not.

    ---
    Note:
    - `bank_account` is company's bank account.
    """
    if search_by == "account_id" and identifier.startswith("acc_"):
        identifier = identifier.removeprefix("acc_")

    return (
        frappe.db.get_value(
            doctype=RAZORPAYX_SETTING,
            filters={
                search_by: identifier,
            },
            fieldname=fields or "name",
            as_dict=as_dict,
        )
        or frappe._dict()
    )


def get_enabled_razorpayx_settings() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_SETTING,
        filters={"disabled": 0},
        pluck="name",
    )


def is_already_paid(amended_from) -> bool | int:
    if not amended_from:
        return False

    return frappe.db.get_value(
        "Payment Entry", amended_from, "make_bank_online_payment"
    )
