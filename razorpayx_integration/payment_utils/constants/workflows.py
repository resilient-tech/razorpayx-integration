"""
Workflows details like actions, states, workflow doctype are defined here.

Which are common for all the payments.

Note: ⚠️ If `Actions` and `States` define elsewhere, then make sure to create them before creating workflows.
"""

from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    FRAPPE_ROLE_PROFILES,
    ROLE_PROFILES,
)


class WORKFLOW_ACTIONS(BaseEnum):
    APPROVE = "Approve"
    HOLD = "Hold"
    REJECT = "Reject"
    REVIEW = "Review"
    SUBMIT = "Submit"
    CANCEL = "Cancel"
    REQUEST_APPROVAL = "Request Approval"


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
    WORKFLOW_STATES.DRAFT.value: "Danger",
    WORKFLOW_STATES.REJECTED.value: "Danger",
    WORKFLOW_STATES.SUBMITTED.value: "Primary",
    WORKFLOW_STATES.PENDING_APPROVAL.value: "Warning",
    WORKFLOW_STATES.CANCELLED.value: "Danger",
}

DEFAULT_WORKFLOW_STATE_FIELD = "payment_integration_workflow_state"


WORKFLOWS = [
    ########### 1. Bank Account ###########
    {
        "workflow_name": "Payment Integration Bank Account Workflow",
        "document_type": "Bank Account",
        "is_active": False,
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": FRAPPE_ROLE_PROFILES.ALL.value,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILES.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILES.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.REJECTED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.CANCELLED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 0,
                "allow_edit": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": ROLE_PROFILES.BANK_ACC_USER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": "All",
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.REJECT.value,
                "next_state": WORKFLOW_STATES.REJECTED.value,
                "allowed": ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.APPROVE.value,
                "next_state": WORKFLOW_STATES.APPROVED.value,
                "allowed": ROLE_PROFILES.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "action": WORKFLOW_ACTIONS.CANCEL.value,
                "next_state": WORKFLOW_STATES.CANCELLED.value,
                "allowed": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
                "allow_self_approval": True,
            },
        ],
        "workflow_state_field": DEFAULT_WORKFLOW_STATE_FIELD,
    },
    ########### 2. Payment Entry ###########
    {
        "workflow_name": "Payment Integration Payment Entry Workflow",
        "document_type": "Payment Entry",
        "is_active": False,
        "send_email": True,
        "states": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": FRAPPE_ROLE_PROFILES.ALL.value,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.REJECTED.value,
                "doc_status": 0,
                "allow_edit": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "doc_status": 1,
                "allow_edit": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATES.CANCELLED.value,
                "doc_status": 2,
                "allow_edit": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": "All",
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.DRAFT.value,
                "action": WORKFLOW_ACTIONS.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "allowed": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.APPROVE.value,
                "next_state": WORKFLOW_STATES.APPROVED.value,
                "allowed": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTIONS.REJECT.value,
                "next_state": WORKFLOW_STATES.REJECTED.value,
                "allowed": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATES.APPROVED.value,
                "action": WORKFLOW_ACTIONS.CANCEL.value,
                "next_state": WORKFLOW_STATES.CANCELLED.value,
                "allowed": FRAPPE_ROLE_PROFILES.SYSTEM_MANAGER.value,
                "allow_self_approval": True,
            },
        ],
        "workflow_state_field": DEFAULT_WORKFLOW_STATE_FIELD,
    },
]
