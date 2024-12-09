from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as BANK_ROLE_PROFILES,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_ROLE_PROFILES,
)
from razorpayx_integration.payment_utils.constants.workflows import (
    WORKFLOW_ACTIONS,
    WORKFLOW_STATES,
)

WORKFLOWS = [
    ########### 1. Bank Account ###########
    {
        "workflow_name": "RazorpayX Bank Account Workflow",
        "document_type": "Bank Account",
        "is_active": True,  # All other workflows become inactive on this DocType
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES.Draft.value,
                "doc_status": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "doc_status": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "doc_status": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Rejected.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Approved.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            # other fields updated with server script: [`is_default`]
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.Draft.value,
                "action": WORKFLOW_ACTIONS.Submit.value,
                "next_state": WORKFLOW_STATES.Submitted.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Reject.value,
                "next_state": WORKFLOW_STATES.Rejected.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Review.value,
                "next_state": WORKFLOW_STATES.Pending_Approval.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES.Approved.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "action": WORKFLOW_ACTIONS.Reject.value,
                "next_state": WORKFLOW_STATES.Rejected.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES.Approved.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
        ],
        "workflow_state_field": "razorpayx_workflow_state",
    },
    ########### 2. Payment Entry ###########
    {
        "workflow_name": "RazorpayX Payment Entry Workflow",
        "document_type": "Payment Entry",
        "is_active": True,  # All other workflows become inactive on this DocType
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES.Draft.value,
                "doc_status": 0,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "doc_status": 1,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "doc_status": 1,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Approved.value,
                "doc_status": 1,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Cancelled.value,
                "doc_status": 2,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Rejected.value,
                "doc_status": 2,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.Draft.value,
                "action": WORKFLOW_ACTIONS.Submit.value,
                "next_state": WORKFLOW_STATES.Submitted.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Review.value,
                "next_state": WORKFLOW_STATES.Pending_Approval.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES.Approved.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "action": WORKFLOW_ACTIONS.Reject.value,
                "next_state": WORKFLOW_STATES.Rejected.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Pending_Approval.value,
                "action": WORKFLOW_ACTIONS.Cancel.value,
                "next_state": WORKFLOW_STATES.Cancelled.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Approve.value,
                "next_state": WORKFLOW_STATES.Approved.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Reject.value,
                "next_state": WORKFLOW_STATES.Rejected.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Submitted.value,
                "action": WORKFLOW_ACTIONS.Cancel.value,
                "next_state": WORKFLOW_STATES.Cancelled.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.Approved.value,
                "action": WORKFLOW_ACTIONS.Cancel.value,
                "next_state": WORKFLOW_STATES.Cancelled.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
        ],
        "workflow_state_field": "razorpayx_workflow_state",
    },
]
