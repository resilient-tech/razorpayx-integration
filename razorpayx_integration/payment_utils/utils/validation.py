import frappe
import requests
from frappe import _

from razorpayx_integration.payment_utils.constants.payments import (
    TRANSFER_METHOD as PAYOUT_MODE,
)


def validate_ifsc_code(ifsc_code: str, throw: bool = False) -> bool | None:
    """
    Validate IFSC Code using Razorpay API.
    """
    response = requests.get(f"https://ifsc.razorpay.com/{ifsc_code}")

    if response.status_code != 200 and throw:
        frappe.throw(
            msg=_("Invalid IFSC Code: <strong>{0}</strong>").format(ifsc_code),
            title=_("Invalid IFSC Code"),
        )

    return response.status_code == 200


def validate_payout_mode(payout_mode: str, throw: bool = False) -> bool | None:
    if PAYOUT_MODE.has_value(payout_mode):
        return True

    if throw:
        frappe.throw(
            msg=_(
                "Invalid Payout Mode: <strong>{0}</strong>. Must be one of: {1}"
            ).format(payout_mode, PAYOUT_MODE.values_as_html_list()),
            title=_("Invalid Payout Mode"),
        )

    return False
