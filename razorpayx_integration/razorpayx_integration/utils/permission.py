import frappe
from frappe import _

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE as INTEGRATION_DOCTYPE,
)
from razorpayx_integration.razorpayx_integration.constants.roles import ROLE_PROFILE


# TODO: need to handle properly, what if there are other integrations and this hook is called?
def has_payout_permissions_for_entries(payment_entries: list[str]) -> bool:
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
    # Check if user has authorizer role
    has_authorizer_role = ROLE_PROFILE.PAYOUT_AUTHORIZER.value in frappe.get_roles()

    if not has_authorizer_role:
        frappe.throw(
            title=_("Insufficient Permissions"),
            msg=_("You do not have permission to make payout."),
            exc=frappe.PermissionError,
        )

    # Check if user has permissions to read integration documents
    frappe.has_permission(INTEGRATION_DOCTYPE, throw=True)
