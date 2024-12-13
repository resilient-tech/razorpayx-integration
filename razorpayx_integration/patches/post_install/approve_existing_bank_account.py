import frappe

from razorpayx_integration.payment_utils.constants.workflows import WORKFLOW_STATES


def execute():
    """
    Approve existing `Bank Account` records.
    """

    BA = frappe.qb.DocType("Bank Account")

    (
        frappe.qb.update(BA)
        .set(BA.razorpayx_workflow_state, WORKFLOW_STATES.APPROVED.value)
        .where(BA.disabled == 0)
        .run()
    )
