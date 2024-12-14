import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_CONTACT_TYPE,
    RAZORPAYX_FUND_ACCOUNT_TYPE,
    RAZORPAYX_PAYOUT_STATUS,
    RAZORPAYX_USER_PAYOUT_MODE,
)


# TODO: need refactoring about enums
def validate_razorpayx_contact_type(type: str):
    """
    :raises ValueError: If the type is not valid.
    """
    if not RAZORPAYX_CONTACT_TYPE.has_value(type):
        type_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_CONTACT_TYPE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid contact type: {0}. <br> Must be one of : <br> {1}").format(
                type, type_list
            ),
            title=_("Invalid {0} Contact Type").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_fund_account_type(type: str):
    """
    :raises ValueError: If the type is not valid.
    """
    if not RAZORPAYX_FUND_ACCOUNT_TYPE.has_value(type):
        type_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_FUND_ACCOUNT_TYPE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Account type: {0}. <br> Must be one of : <br> {1}").format(
                type, type_list
            ),
            title=_("Invalid {0} Fund Account type").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_payout_mode(mode: str):
    """
    :raises ValueError: If the mode is not valid.
    """
    if not RAZORPAYX_USER_PAYOUT_MODE.has_value(mode):
        mode_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_USER_PAYOUT_MODE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Payout mode: {0}.<br> Must be one of : <br> {1}").format(
                mode, mode_list
            ),
            title=_("Invalid {0} Payout mode").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_payout_status(status: str):
    """
    :raises ValueError: If the status is not valid.
    """
    if not RAZORPAYX_PAYOUT_STATUS.has_value(status):
        status_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_PAYOUT_STATUS)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Payout status: {0}.<br> Must be one of : <br> {1}").format(
                status, status_list
            ),
            title=_("Invalid {0} Payout status").format(RAZORPAYX),
            exc=ValueError,
        )
