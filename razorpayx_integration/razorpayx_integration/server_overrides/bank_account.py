# TODO: validate if bank account is referenced in any transaction / payment entry. If yes, then do not allow to update/delete it. Error: Create a new bank account and make it default and disable this account.

from razorpayx_integration.constants.workflows import WORKFLOW_STATES


def validate(doc, method=None):
    toggle_is_default(doc)


def toggle_is_default(doc):
    """
    Make the `Bank Account` default based on workflow state.

    - Rejected: Make the `Bank Account` non-default
    - Approved: Make the `Bank Account` default
    """
    if doc.workflow_state == WORKFLOW_STATES["Rejected"][0]:
        doc.is_default = 0
    elif doc.workflow_state == WORKFLOW_STATES["Approved"][0]:
        doc.is_default = 1
