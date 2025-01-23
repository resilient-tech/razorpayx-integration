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

    :param payment_entries: List of payment entries.

    ---
    Checks:
    - User has role of payout authorizer.
    - User can read integration documents.
    - User have permissions to submit the PE.
    """
    has_payment_authorizer_role(throw=True)

    has_integration_access(docname=None, throw=True)

    # TODO: how to check for `Company Bank Account`?
    has_payment_entry_access(payment_entries, permission="submit", throw=True)


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


def has_payment_entry_access(
    payment_entries: str | list[str] | None = None,
    *,
    permission: Literal["submit", "cancel"] = "submit",
    throw=False,
) -> bool | None:
    """
    Check if user can submit/cancel the payment entries.

    :param payment_entries: Payment Entry name or list of names.
    :param permission: Permission type to check.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.

    ---
    If any single PE doesn't have permission, returns `False`.
    """
    if not payment_entries:
        return frappe.has_permission(
            doctype="Payment Entry", ptype=permission, throw=throw
        )
    else:
        if isinstance(payment_entries, str):
            payment_entries = [payment_entries]

        for pe in payment_entries:
            access = frappe.has_permission(
                doctype="Payment Entry", doc=pe, ptype=permission, throw=throw
            )

            # If any single PE doesn't have permission, return False.
            if not access:
                return False

        return True


def user_has_payout_permissions(
    payment_entries: str | list[str] | None = None,
    razorpayx_account: str | None = None,
    *,
    pe_permission: Literal["submit", "cancel"] = "submit",
    throw: bool = False,
):
    """
    Check user has payout permissions or not!

    :param payment_entries: Payment Entry name or list of names.
    :param razorpayx_account: RazorPayX account (Integration docname).
    :param pe_permission: Payment entry permission to check.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.


    ---
    Checks:
    - User has role of payout authorizer.
    - User can read integration documents.
    - User have permissions to submit/cancel the PE.
    """
    # 1. Check if user has payment authorizer role.
    has_role = has_payment_authorizer_role(throw=throw)

    # 2. Check if user can read the integration.
    has_rpx_access = has_integration_access(docname=razorpayx_account, throw=throw)

    # 3. Check if user has access to submit/cancel the payment entries.
    has_pe_access = has_payment_entry_access(
        payment_entries, permission=pe_permission, throw=throw
    )

    return bool(has_role and has_rpx_access and has_pe_access)
