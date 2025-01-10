import json

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE


@frappe.whitelist()
def get_razorpayx_account_from_company_bank_account(
    company_bank_account: str,
) -> str | None:
    """
    Fetch the RazorpayX Account Integration name from the Company Bank Account.

    :param company_bank_account: Company Bank Account.
    """
    frappe.has_permission(RAZORPAYX_INTEGRATION_DOCTYPE, throw=True)

    return frappe.db.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        {"bank_account": company_bank_account},
        "name",
    )


@frappe.request_cache
def get_razorpayx_account_from_account_id(account_id: str) -> str | None:
    """
    Get the account integration name from the account id.

    :param account_id: RazorpayX Account ID (Business ID).

    ---
    Note: `account_id` should be in the format `acc_XXXXXX`.
    """
    return frappe.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        {"account_id": account_id.removeprefix("acc_")},
        "name",
    )


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )
