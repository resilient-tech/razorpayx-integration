import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from razorpayx_integration.payment_utils.constants.custom_fields import CUSTOM_FIELDS
from razorpayx_integration.payment_utils.constants.property_setters import (
    PROPERTY_SETTERS,
)
from razorpayx_integration.payment_utils.constants.roles import ROLES
from razorpayx_integration.payment_utils.constants.workflows import (
    STATES_COLORS as WORKFLOW_STATES,
)
from razorpayx_integration.payment_utils.constants.workflows import (
    WORKFLOW_ACTION,
    WORKFLOWS,
)
from razorpayx_integration.payment_utils.utils import (
    delete_custom_fields,
    delete_property_setters,
    delete_role_and_permissions,
    make_roles_and_permissions,
    make_workflow_actions,
    make_workflow_states,
    make_workflows,
)


################### After Install Setup ###################
def make_payment_utils_roles_and_permissions():
    make_roles_and_permissions(ROLES)


def make_payment_utils_custom_fields():
    create_custom_fields(CUSTOM_FIELDS)


def make_payment_utils_property_setters():
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


def make_payment_utils_workflows():
    """
    Note: ⚠️ All `Payment Utils` workflow `states` and `actions` also created here.

    So, no need to create them separately again.
    """

    # create states
    make_workflow_states(WORKFLOW_STATES)

    # create actions
    make_workflow_actions(WORKFLOW_ACTION.values())

    # create workflows
    make_workflows(WORKFLOWS)


################### Before Uninstall Setup ###################
def delete_payment_utils_custom_fields():
    delete_custom_fields(CUSTOM_FIELDS)


def delete_payment_utils_property_setters():
    delete_property_setters(PROPERTY_SETTERS)


def delete_payment_utils_role_and_permissions():
    # TODO
    delete_role_and_permissions(ROLES)
