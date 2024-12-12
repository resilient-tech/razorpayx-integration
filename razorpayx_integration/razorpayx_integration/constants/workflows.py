from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_ROLE_PROFILES,
)
from razorpayx_integration.payment_utils.constants.workflows import (
    WORKFLOW_ACTIONS,
    WORKFLOW_STATES,
)
from razorpayx_integration.razorpayx_integration.constants.roles import (
    ROLE_PROFILES as BANK_ROLE_PROFILES,
)

# ? can use `ALL` instead of `BANK_ROLE_PROFILES.BANK_ACC_USER.value` to allow all roles
# TODO: more efficient and robust
WORKFLOWS = [
    ########### 1. Bank Account ###########
    {
        "workflow_name": "RazorpayX Bank Account Workflow",
        "document_type": "Bank Account",
        "is_active": True,  # All other workflows become inactive on this DocType
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATES.SUBMITTED.value,
                "doc_status": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "doc_status": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.REJECTED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.CANCELLED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 0,
                "allow_edit": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            # other fields updated with server script: [`is_default`]
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.SUBMIT.value,
                "next_state": WORKFLOW_STATES.SUBMITTED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_USER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.SUBMIT.value,
                "next_state": WORKFLOW_STATES.SUBMITTED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.SUBMITTED.value,
                "action": WORKFLOW_ACTIONS.REJECT.value,
                "next_state": WORKFLOW_STATES.REJECTED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.SUBMITTED.value,
                "action": WORKFLOW_ACTIONS.REVIEW.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.SUBMITTED.value,
                "action": WORKFLOW_ACTIONS.APPROVE.value,
                "next_state": WORKFLOW_STATES.APPROVED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.REJECT.value,
                "next_state": WORKFLOW_STATES.REJECTED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.APPROVE.value,
                "next_state": WORKFLOW_STATES.APPROVED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "action": WORKFLOW_ACTIONS.CANCEL.value,
                "next_state": WORKFLOW_STATES.CANCELLED.value,
                "allowed": BANK_ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
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
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": "All",
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "doc_status": 0,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.REJECTED.value,
                "doc_status": 0,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "doc_status": 1,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.CANCELLED.value,
                "doc_status": 2,
                "allow_edit": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.SUBMIT.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": "All",
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.SUBMIT.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.APPROVE.value,
                "next_state": WORKFLOW_STATES.APPROVED.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.REJECT.value,
                "next_state": WORKFLOW_STATES.REJECTED.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "action": WORKFLOW_ACTIONS.CANCEL.value,
                "next_state": WORKFLOW_STATES.CANCELLED.value,
                "allowed": PAYMENT_ROLE_PROFILES.PAYMENT_MANAGER.value,
                "allow_self_approval": True,
            },
        ],
        "workflow_state_field": "razorpayx_workflow_state",
    },
]
