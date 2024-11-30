from razorpayx_integration.constants.enums import BaseEnum
from razorpayx_integration.constants.roles import ROLE_PROFILE


# TODO: Payment Entry Workflow Action remaining
class WORKFLOW_ACTIONS(BaseEnum):
    Approve = "Approve"
    Hold = "Hold"
    Reject = "Reject"
    Review = "Review"
    Submit = "Submit"


# TODO: Payment Entry Workflow State remaining
# * Note: Enum can't be used here as the values are not unique
WORKFLOW_STATES = {
    "Approved": ["Approved", "Success"],
    "Pending": ["Pending", "Warning"],
    "Draft": ["Draft", "Warning"],
    "Rejected": ["Rejected", "Danger"],
    "Submitted": ["Submitted", "Primary"],
}

# TODO: Payment Entry Workflow remaining
WORKFLOWS = [
    {
        "workflow_name": "RazorpayX Bank Account Workflow",
        "document_type": "Bank Account",
        "is_active": True,  # All other workflows become inactive on this DocType
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES["Draft"][0],
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATES["Submitted"][0],
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Pending"][0],
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Rejected"][0],
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Rejected"][0],
                "doc_status": 0,
                "update_field": "is_default",
                "update_value": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Approved"][0],
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Approved"][0],
                "doc_status": 0,
                "update_field": "is_default",
                "update_value": 1,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES["Draft"][0],
                "action": WORKFLOW_ACTIONS.Submit.value,
                "next_state": WORKFLOW_STATES["Submitted"][0],
                "allowed": ROLE_PROFILE.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATES["Submitted"][0],
                "action": WORKFLOW_ACTIONS.Reject.value,
                "next_state": WORKFLOW_STATES["Rejected"][0],
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Submitted"][0],
                "action": WORKFLOW_ACTIONS.Review.value,
                "next_state": WORKFLOW_STATES["Pending"][0],
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Submitted"][0],
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES["Approved"][0],
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Pending"][0],
                "action": WORKFLOW_ACTIONS.Reject.value,
                "next_state": WORKFLOW_STATES["Rejected"][0],
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES["Pending"][0],
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES["Approved"][0],
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
        ],
        "workflow_state_field": "workflow_state",
    }
]
