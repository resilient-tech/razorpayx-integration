import re

import frappe
from frappe import _

from razorpayx_integration.razorpayx_integration.constants.payouts import (
    DESCRIPTION_REGEX,
    RAZORPAYX_CONTACT_TYPE,
    RAZORPAYX_FUND_ACCOUNT_TYPE,
    RAZORPAYX_PAYOUT_LINK_STATUS,
    RAZORPAYX_PAYOUT_MODE,
    RAZORPAYX_PAYOUT_STATUS,
    RAZORPAYX_USER_PAYOUT_MODE,
)


def validate_razorpayx_contact_type(type: str):
    """
    :raises frappe.ValidationError: If the type is not valid.
    """
    if RAZORPAYX_CONTACT_TYPE.has_value(type):
        return

    frappe.throw(
        msg=_("Invalid contact type: {0}. <br> Must be one of : <br> {1}").format(
            type, RAZORPAYX_CONTACT_TYPE.values_as_html_list()
        ),
        title=_("Invalid RazorPayX Contact Type"),
        exc=frappe.ValidationError,
    )


def validate_razorpayx_fund_account_type(type: str):
    """
    :raises frappe.ValidationError: If the type is not valid.
    """
    if RAZORPAYX_FUND_ACCOUNT_TYPE.has_value(type):
        return

    frappe.throw(
        msg=_("Invalid Account type: {0}. <br> Must be one of : <br> {1}").format(
            type, RAZORPAYX_FUND_ACCOUNT_TYPE.values_as_html_list()
        ),
        title=_("Invalid RazorPayX Fund Account type"),
        exc=frappe.ValidationError,
    )


def validate_razorpayx_payout_mode(mode: str | None = None):
    """
    :raises frappe.ValidationError: If the mode is not valid.
    """
    if RAZORPAYX_PAYOUT_MODE.has_value(mode):
        return

    frappe.throw(
        msg=_("Invalid Payout mode: {0}.<br> Must be one of : <br> {1}").format(
            mode, RAZORPAYX_PAYOUT_MODE.values_as_html_list()
        ),
        title=_("Invalid RazorPayX Payout mode"),
        exc=frappe.ValidationError,
    )


def validate_razorpayx_user_payout_mode(mode: str | None = None):
    """
    :raises frappe.ValidationError: If the mode is not valid.
    """
    if RAZORPAYX_USER_PAYOUT_MODE.has_value(mode):
        return

    frappe.throw(
        msg=_("Invalid Payout mode: {0}.<br> Must be one of : <br> {1}").format(
            mode, RAZORPAYX_USER_PAYOUT_MODE.values_as_html_list()
        ),
        title=_("Invalid RazorPayX Payout mode"),
        exc=frappe.ValidationError,
    )


def validate_razorpayx_payout_status(status: str):
    """
    :raises frappe.ValidationError: If the status is not valid.
    """
    if RAZORPAYX_PAYOUT_STATUS.has_value(status):
        return

    frappe.throw(
        msg=_("Invalid Payout status: {0}.<br> Must be one of : <br> {1}").format(
            status, RAZORPAYX_PAYOUT_STATUS.values_as_html_list()
        ),
        title=_("Invalid RazorPayX Payout status"),
        exc=frappe.ValidationError,
    )


def validate_razorpayx_payout_link_status(status: str):
    """
    :raises frappe.ValidationError: If the status is not valid.
    """
    if RAZORPAYX_PAYOUT_LINK_STATUS.has_value(status):
        return

    frappe.throw(
        msg=_("Invalid Payout Link status: {0}.<br> Must be one of : <br> {1}").format(
            status, RAZORPAYX_PAYOUT_LINK_STATUS.values_as_html_list()
        ),
        title=_("Invalid RazorPayX Payout Link status"),
        exc=frappe.ValidationError,
    )


def validate_razorpayx_payout_description(description: str):
    """
    Description/Narration should be of max 30 characters and A-Z, a-z, 0-9, and space only.

    :raises frappe.ValidationError: If the description is not valid.
    """
    pattern = re.compile(DESCRIPTION_REGEX)

    if pattern.match(description):
        return

    frappe.throw(
        msg=_(
            "Invalid Description: {0}.<br> Must be alphanumeric and space only with max 30 characters"
        ).format(description),
        title=_("Invalid RazorPayX Payout Description"),
        exc=frappe.ValidationError,
    )
