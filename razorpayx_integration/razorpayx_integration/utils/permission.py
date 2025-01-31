from typing import Literal

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_SETTING
from razorpayx_integration.payment_utils.constants.roles import ROLE_PROFILE


def before_payment_authentication(payment_entries: list[str]) -> None:
    """
    Before OTP generation, check if user has permissions to authenticate the payment.

    It is hook used by `Payment Utils`
    """
    has_payout_permissions(payment_entries, throw=True)


def has_payout_permissions(
    payment_entries: str | list[str] | None = None,
    *,
    ptype: Literal["submit", "cancel"] = "submit",
    throw: bool = False,
):
    """
    Check current user has payout permissions or not!

    :param payment_entries: Payment Entry name or list of names.
    :param ptype: Payment entry permission to check.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.

    ---
    Checks:
    - User has role of payout authorizer.
    - User can read integration documents.
    - User have permissions to submit/cancel the PE.
    """
    authorizer_role = has_payment_authorizer_role(throw=throw)
    permission = has_payment_entry_permission(payment_entries, ptype=ptype, throw=throw)

    return bool(authorizer_role and permission)


def has_payment_authorizer_role(*, throw=False) -> bool | None:
    authorizer_role = ROLE_PROFILE.PAYMENT_AUTHORIZER.value in frappe.get_roles()

    if not authorizer_role and throw:
        frappe.throw(
            title=_("Permission Error"),
            msg=_("You don't have permission to authorize the payment."),
            exc=frappe.PermissionError,
        )

    return authorizer_role


def has_payment_entry_permission(
    payment_entries: str | list[str] | None = None,
    *,
    ptype: Literal["submit", "cancel"] = "submit",
    throw=False,
) -> bool | None:
    """
    Check if user can submit/cancel the payment entries.
    Also checks for RazorPayX Integration Setting permission.

    :param payment_entries: Payment Entry name or list of names.
    :param ptype: Permission type to check.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.

    ---
    If any single PE doesn't have permission, returns `False`.
    """
    if not payment_entries:
        pe_permission = frappe.has_permission("Payment Entry", ptype, throw=throw)
        rpx_permission = frappe.has_permission(doctype=RAZORPAYX_SETTING, throw=throw)

        return bool(pe_permission and rpx_permission)

    else:
        if isinstance(payment_entries, str):
            payment_entries = [payment_entries]

        # RazorPayX Integration Setting.
        razorpayx_settings = set(
            frappe.get_all(
                "Payment Entry",
                filters={"name": ("in", payment_entries)},
                pluck="integration_docname",
            )
        )

        if not razorpayx_settings:
            if throw:
                frappe.throw(
                    title=_("Integration Settings Not Found"),
                    msg=_("Please select valid Payment Entries to make payout."),
                    exc=frappe.DoesNotExistError,
                )

            return False

        for setting in razorpayx_settings:
            permission = frappe.has_permission(
                RAZORPAYX_SETTING, doc=setting, throw=throw
            )

            if not permission:
                return False

        # Payment Entry.
        for pe in payment_entries:
            permission = frappe.has_permission("Payment Entry", ptype, pe, throw=throw)

            if not permission:
                return False

        return True
