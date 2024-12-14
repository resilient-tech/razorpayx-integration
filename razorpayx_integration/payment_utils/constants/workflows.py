"""
Workflows details like actions, states, workflow doctype are defined here.

Which are common for all the payments.

Note: ⚠️ If `Actions` and `States` define elsewhere, then make sure to create them before creating workflows.
"""

from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    FRAPPE_ROLE_PROFILE,
    ROLE_PROFILE,
)


class WORKFLOW_ACTION(BaseEnum):
    APPROVE = "Approve"
    HOLD = "Hold"
    REJECT = "Reject"
    REVIEW = "Review"
    SUBMIT = "Submit"
    CANCEL = "Cancel"
    REQUEST_APPROVAL = "Request Approval"


class WORKFLOW_STATE(BaseEnum):
    APPROVED = "Approved"
    PENDING = "Pending"
    DRAFT = "Draft"
    REJECTED = "Rejected"
    SUBMITTED = "Submitted"
    PENDING_APPROVAL = "Pending Approval"
    CANCELLED = "Cancelled"


STATES_COLORS = {
    WORKFLOW_STATE.APPROVED.value: "Success",
    WORKFLOW_STATE.PENDING.value: "Warning",
    WORKFLOW_STATE.DRAFT.value: "Danger",
    WORKFLOW_STATE.REJECTED.value: "Danger",
    WORKFLOW_STATE.SUBMITTED.value: "Primary",
    WORKFLOW_STATE.PENDING_APPROVAL.value: "Warning",
    WORKFLOW_STATE.CANCELLED.value: "Danger",
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
                "state": WORKFLOW_STATE.DRAFT.value,
                "doc_status": 0,
                "allow_edit": FRAPPE_ROLE_PROFILE.ALL.value,
            },
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_USER.value,
            },
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.BANK_ACC_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.REJECTED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.CANCELLED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 1,
                "allow_edit": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.APPROVED.value,
                "doc_status": 0,
                "update_field": "disabled",
                "update_value": 0,
                "allow_edit": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "action": WORKFLOW_ACTION.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "allowed": ROLE_PROFILE.BANK_ACC_USER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "action": WORKFLOW_ACTION.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "action": WORKFLOW_ACTION.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "allowed": "All",
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTION.REJECT.value,
                "next_state": WORKFLOW_STATE.REJECTED.value,
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTION.APPROVE.value,
                "next_state": WORKFLOW_STATE.APPROVED.value,
                "allowed": ROLE_PROFILE.BANK_ACC_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.APPROVED.value,
                "action": WORKFLOW_ACTION.CANCEL.value,
                "next_state": WORKFLOW_STATE.CANCELLED.value,
                "allowed": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
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
                "state": WORKFLOW_STATE.DRAFT.value,
                "doc_status": 0,
                "allow_edit": FRAPPE_ROLE_PROFILE.ALL.value,
            },
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "doc_status": 0,
                "allow_edit": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.REJECTED.value,
                "doc_status": 0,
                "allow_edit": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.APPROVED.value,
                "doc_status": 1,
                "allow_edit": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
            },
            {
                "state": WORKFLOW_STATE.CANCELLED.value,
                "doc_status": 2,
                "allow_edit": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
            },
        ],
        "transitions": [
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "action": WORKFLOW_ACTION.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "allowed": "All",
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.DRAFT.value,
                "action": WORKFLOW_ACTION.REQUEST_APPROVAL.value,
                "next_state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "allowed": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTION.APPROVE.value,
                "next_state": WORKFLOW_STATE.APPROVED.value,
                "allowed": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.PENDING_APPROVAL.value,
                "action": WORKFLOW_ACTION.REJECT.value,
                "next_state": WORKFLOW_STATE.REJECTED.value,
                "allowed": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
                "allow_self_approval": True,
            },
            {
                "state": WORKFLOW_STATE.APPROVED.value,
                "action": WORKFLOW_ACTION.CANCEL.value,
                "next_state": WORKFLOW_STATE.CANCELLED.value,
                "allowed": FRAPPE_ROLE_PROFILE.SYSTEM_MANAGER.value,
                "allow_self_approval": True,
            },
        ],
        "workflow_state_field": DEFAULT_WORKFLOW_STATE_FIELD,
    },
]
