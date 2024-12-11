"""
Workflows details like actions, states, workflow doctype are defined here.

Which are common for all the payments.

Note: ⚠️ If `Actions` and `States` define elsewhere, then make sure to create them before creating workflows.
"""

from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class WORKFLOW_ACTIONS(BaseEnum):
    APPROVE = "Approve"
    HOLD = "Hold"
    REJECT = "Reject"
    REVIEW = "Review"
    SUBMIT = "Submit"
    CANCEL = "Cancel"


class WORKFLOW_STATES(BaseEnum):
    APPROVED = "Approved"
    PENDING = "Pending"
    DRAFT = "Draft"
    REJECTED = "Rejected"
    SUBMITTED = "Submitted"
    PENDING_APPROVAL = "Pending Approval"
    CANCELLED = "Cancelled"


STATES_COLORS = {
    WORKFLOW_STATES.APPROVED.value: "Success",
    WORKFLOW_STATES.PENDING.value: "Warning",
    WORKFLOW_STATES.DRAFT.value: "Warning",
    WORKFLOW_STATES.REJECTED.value: "Danger",
    WORKFLOW_STATES.SUBMITTED.value: "Primary",
    WORKFLOW_STATES.PENDING_APPROVAL.value: "Warning",
    WORKFLOW_STATES.CANCELLED.value: "Danger",
}


WORKFLOWS = []
