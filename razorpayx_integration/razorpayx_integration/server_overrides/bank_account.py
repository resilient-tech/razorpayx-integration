# TODO: validate if bank account is referenced in any transaction / payment entry. If yes, then do not allow to update/delete it. Error: Create a new bank account and make it default and disable this account.
import frappe
from frappe import _

from razorpayx_integration.razorpayx_integration.constants.workflows import (
    WORKFLOW_STATES,
)

REJECTED_STATES = [
    WORKFLOW_STATES.REJECTED.value,
    WORKFLOW_STATES.CANCELLED.value,
]


# TODO: move to utils
# TODO: depends on workflpw is on or not
def validate(doc, method=None):
    validate_rejected_states(doc)


def validate_rejected_states(doc):
    """
    Throws an error if the `Bank Account` is in rejected states and the user tries to update it.

    - Rejected states: `Rejected`, `Cancelled`
    """
    previous_doc = doc.get_doc_before_save() or frappe._dict()

    if previous_doc.razorpayx_workflow_state not in REJECTED_STATES:
        return

    frappe.throw(title=_("Invalid Operation"), msg=_("Cannot Update Bank Account"))
