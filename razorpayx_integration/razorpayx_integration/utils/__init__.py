from typing import Literal

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE


# TODO: use this function to get the RazorpayX Account Integration name
@frappe.request_cache
def get_razorpayx_account(
    identifier: str,
    search_by: Literal["bank_account", "account_id"],
    fields: list[str] | None = None,
    as_dict: bool = True,
) -> dict[str, str] | None:
    """
    Fetch the RazorpayX Account Integration name based on the identifier.

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

    return frappe.db.get_value(
        doctype=RAZORPAYX_INTEGRATION_DOCTYPE,
        filters={
            search_by: identifier,
        },
        fieldname=fields or "name",
        as_dict=as_dict,
    )


@frappe.whitelist()
def get_razorpayx_account_by_bank_account(bank_account: str) -> str | None:
    """
    Get the RazorpayX Account Integration name based on the bank account.

    :param bank_account: Company's bank account.
    """
    frappe.has_permission("Payment Entry", throw=True)

    account = get_razorpayx_account(bank_account, "bank_account")

    return account.get("name") if account else None


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )
