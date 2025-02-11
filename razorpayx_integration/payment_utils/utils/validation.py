import frappe
import requests
from frappe import _


def validate_ifsc_code(ifsc_code: str, throw=True) -> bool | None:
    """
    Validate IFSC Code using Razorpay API.

    :param ifsc_code: IFSC Code to validate.
    :param throw: Raise exception if IFSC Code is invalid.
    """
    response = requests.get(f"https://ifsc.razorpay.com/{ifsc_code}")

    if response.status_code != 200 and throw:
        frappe.throw(
            msg=_("Invalid IFSC Code: <strong>{0}</strong>").format(ifsc_code),
            title=_("Invalid IFSC Code"),
        )

    return response.status_code == 200
