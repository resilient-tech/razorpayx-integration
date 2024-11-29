from razorpayx_integration.constants.enums import BaseEnum
from razorpayx_integration.constants.roles import ROLE_PROFILE


# TODO: Payment Entry Workflow State remaining
class WORKFLOW_STATES(BaseEnum):
    """
    Note: Use as `WORKFLOW_STATE.<STATE>.name` to get the state name
    """

    Pending = "Warning"
    Approved = "Success"
    Rejected = "Danger"


# TODO: Payment Entry Workflow Action remaining
class WORKFLOW_ACTIONS(BaseEnum):
    Approve = "Approve"
    Reject = "Reject"
    Review = "Review"
    Hold = "Hold"


# TODO: Payment Entry Workflow remaining
WORKFLOWS = [
    {
        "workflow_name": "RazorpayX Bank Account Workflow",
        "document_type": "Bank Account",
        "is_active": True,  # All other workflows become inactive on this DocType
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES.Pending.name,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Approved.name,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.Pending.name,
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES.Approved.name,
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            }
        ],
        "workflow_state_field": "workflow_state",
    }
]
