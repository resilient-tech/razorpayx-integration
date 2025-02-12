import frappe
from frappe import _

from razorpayx_integration.payment_utils.constants.roles import ROLE_PROFILE


def has_payout_permissions(payment_entries: str | list[str], throw: bool = False):
    """
    Check current user has payout permissions or not!

    :param payment_entries: Payment Entry name or list of names.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.

    ---
    Checks:
    - User has role of payout authorizer.
    - User can read integration documents.
    - User have permissions to submit/cancel the PE.
    """
    if frappe.session.user == "Administrator":
        if throw:
            frappe.throw(
                msg=_("Administrator can't authorize the payout."),
                title=_("Permission Error"),
                exc=frappe.PermissionError,
            )

        return False

    authorizer_role = has_payment_authorizer_role(throw=throw)
    permission = has_payment_entry_permission(payment_entries, throw=throw)

    return bool(authorizer_role and permission)


def has_payment_authorizer_role(*, throw=False) -> bool | None:
    has_authorizer_role = ROLE_PROFILE.PAYMENT_AUTHORIZER.value in frappe.get_roles()

    if not has_authorizer_role and throw:
        frappe.throw(
            title=_("Permission Error"),
            msg=_("You don't have permission to authorize the payment."),
            exc=frappe.PermissionError,
        )

    return has_authorizer_role


def has_payment_entry_permission(
    payment_entries: str | list[str], *, throw=False
) -> bool | None:
    """
    Check if user can submit/cancel the payment entries.
    Also checks for RazorpayX Integration Setting permission.

    :param payment_entries: Payment Entry name or list of names.
    :param throw: If `True`, throws `PermissionError` if user doesn't have access.

    ---
    If any single PE doesn't have permission, returns `False`.
    """
    if isinstance(payment_entries, str):
        payment_entries = [payment_entries]

    # Integration Setting.
    integration_settings = set(
        frappe.get_all(
            "Payment Entry",
            filters={"name": ("in", payment_entries)},
            fields=("integration_doctype", "integration_docname"),
            as_list=True,
        )
    )

    if not integration_settings:
        if throw:
            frappe.throw(
                title=_("Integration Settings Not Found"),
                msg=_("Please select valid Payment Entries to make payout."),
                exc=frappe.DoesNotExistError,
            )

        return False

    for doctype, docname in integration_settings:
        # integration setting is not set
        if not doctype or not docname:
            continue

        permission = frappe.has_permission(doctype, doc=docname, throw=throw)

        if not permission:
            return False

    # Payment Entry.
    for pe in payment_entries:
        permission = frappe.has_permission("Payment Entry", "submit", pe, throw=throw)

        if not permission:
            return False

    return True
