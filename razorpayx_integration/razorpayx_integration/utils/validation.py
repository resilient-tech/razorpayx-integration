import re

import frappe
from frappe import _

from razorpayx_integration.razorpayx_integration.constants.payouts import (
    DESCRIPTION_REGEX,
    FUND_ACCOUNT_TYPE,
)


def validate_fund_account_type(type: str):
    """
    :raises frappe.ValidationError: If the type is not valid.
    """
    if FUND_ACCOUNT_TYPE.has_value(type):
        return

    frappe.throw(
        msg=_("Invalid Account type: {0}. <br> Must be one of : <br> {1}").format(
            type, FUND_ACCOUNT_TYPE.values_as_html_list()
        ),
        title=_("Invalid RazorpayX Fund Account type"),
        exc=frappe.ValidationError,
    )


def validate_payout_description(description: str):
    """
    Description/Narration should be of max 30 characters and A-Z, a-z, 0-9, and space only.

    Standard RazorpayX Payout Description/Narration validation.

    :raises frappe.ValidationError: If the description is not valid.
    """
    pattern = re.compile(DESCRIPTION_REGEX)

    if pattern.match(description):
        return

    frappe.throw(
        msg=_(
            "Must be <strong>alphanumeric</strong> and contain <strong>spaces</strong> only, with a maximum of <strong>30</strong> characters."
        ),
        title=_("Invalid RazorpayX Payout Description"),
        exc=frappe.ValidationError,
    )
