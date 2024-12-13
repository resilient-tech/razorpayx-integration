# TODO: validate if bank account is referenced in any transaction / payment entry. If yes, then do not allow to update/delete it. Error: Create a new bank account and make it default and disable this account.
import frappe
from frappe import _

from razorpayx_integration.razorpayx_integration.constants.workflows import (
    WORKFLOW_STATES,
)

# TODO: After Approve, only allow `disabled` and `is_default` to be updated.

rejected_states = [
    WORKFLOW_STATES.REJECTED.value,
    WORKFLOW_STATES.CANCELLED.value,
]

final_states = [
    WORKFLOW_STATES.APPROVED.value,
    *rejected_states,
]


def validate(doc, method=None):
    validate_final_states(doc)
    toggle_default(doc)


def toggle_default(doc):
    """
    Make the `Bank Account` default based on workflow state.

    - Rejected | Cancelled: Make the `Bank Account` non-default
    - Approved: Make the `Bank Account` default
    """
    if doc.razorpayx_workflow_state in rejected_states:
        doc.is_default = 0
    elif doc.razorpayx_workflow_state == WORKFLOW_STATES.APPROVED.value:
        doc.is_default = 1


def validate_final_states(doc):
    """
    Throws an error if the `Bank Account` is in final states and the user tries to update it.

    - Final states: `Approved`, `Rejected`, `Cancelled`
    """
    previous_doc = doc.get_doc_before_save() or frappe._dict()

    if previous_doc.razorpayx_workflow_state not in final_states:
        return

    frappe.throw(title=_("Invalid Operation"), msg=_("Cannot Update Bank Account"))
