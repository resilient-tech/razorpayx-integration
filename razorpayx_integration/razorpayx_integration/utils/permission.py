from typing import Literal

import frappe
from frappe import _

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE as INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.roles import ROLE_PROFILE


# TODO: need to handle properly, what if there are other integrations and this hook is called?
def before_payment_authentication(payment_entries: list[str]) -> bool:
    """
    Hook to check if the user has permissions to make payouts for the given payment entries.

    Calls when authentication via OTP/Password is required for making payouts.

    Throws `PermissionError` if the user doesn't have permissions.

    ---
    Checks:
    - User has role of payout authorizer.
    - User can read integration documents.
    - For each PE, checks bank account it must be connected with razorpayx account.
    - User have permissions to submit the PE.

    :param payment_entries: List of payment entries.
    """
    has_payment_authorizer_role(throw=True)

    has_integration_access(docname=None, throw=True)

    # TODO: how to check for `Company Bank Account`?
    has_pe_access(payment_entries, permission="submit", throw=True)


def has_payment_authorizer_role(*, throw=False) -> bool | None:
    """
    Check user have payment authorizer role or not!

    :param throw: If `True`, throws `PermissionError` if user doesn't have authorizer role.
    """
    has_authorizer_role = ROLE_PROFILE.PAYMENT_AUTHORIZER.value in frappe.get_roles()

    if not has_authorizer_role and throw:
        frappe.throw(
            title=_("Insufficient Permissions"),
            msg=_("You do not have permission to make payout."),
            exc=frappe.PermissionError,
        )

    return has_authorizer_role


def has_integration_access(*, docname: str | None = None, throw=False) -> bool | None:
    """
    Check if user can read the integration.

    :param docname: RazorPayX account (docname).
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.
    """
    return frappe.has_permission(doctype=INTEGRATION_DOCTYPE, doc=docname, throw=throw)


def has_pe_access(
    payment_entries: str | list[str],
    permission: Literal["submit", "cancel"] = "submit",
    throw=False,
) -> bool | None:
    """
    Check if user can submit/cancel the payment entries.

    :param payment_entries: Payment Entry name or list of names.
    :param permission: Permission type to check.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.
    """
    if isinstance(payment_entries, str):
        payment_entries = [payment_entries]

    for pe in payment_entries:
        frappe.has_permission(
            doctype="Payment Entry", doc=pe, ptype=permission, throw=throw
        )

    return True
