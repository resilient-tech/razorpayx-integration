"""
Workflows details like actions, states, workflow doctype are defined here.

Which are common for all the payment related doctypes.

Note: ⚠️ Do not define `Actions` and `States` somewhere else.
"""

from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class WORKFLOW_ACTIONS(BaseEnum):
    Approve = "Approve"
    Hold = "Hold"
    Reject = "Reject"
    Review = "Review"
    Submit = "Submit"
    Cancel = "Cancel"


class WORKFLOW_STATES(BaseEnum):
    Approved = "Approved"
    Pending = "Pending"
    Draft = "Draft"
    Rejected = "Rejected"
    Submitted = "Submitted"
    Pending_Approval = "Pending Approval"
    Cancelled = "Cancelled"


STATES_COLORS = {
    WORKFLOW_STATES.Approved.value: "Success",
    WORKFLOW_STATES.Pending.value: "Warning",
    WORKFLOW_STATES.Draft.value: "Warning",
    WORKFLOW_STATES.Rejected.value: "Danger",
    WORKFLOW_STATES.Submitted.value: "Primary",
    WORKFLOW_STATES.Pending_Approval.value: "Warning",
    WORKFLOW_STATES.Cancelled.value: "Danger",
}


WORKFLOWS = []
