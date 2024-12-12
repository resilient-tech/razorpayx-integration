import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from razorpayx_integration.payment_utils.utils import (
    delete_custom_fields,
    delete_property_setters,
    delete_role_and_permissions,
    delete_workflows,
    make_roles_and_permissions,
    make_workflows,
)
from razorpayx_integration.razorpayx_integration.constants.custom_fields import (
    CUSTOM_FIELDS,
)
from razorpayx_integration.razorpayx_integration.constants.property_setters import (
    PROPERTY_SETTERS,
)
from razorpayx_integration.razorpayx_integration.constants.roles import ROLES
from razorpayx_integration.razorpayx_integration.constants.workflows import WORKFLOWS


################### After Install Setup ###################
def make_razorpayx_roles_and_permissions():
    make_roles_and_permissions(ROLES)


def make_razorpayx_custom_fields():
    create_custom_fields(CUSTOM_FIELDS)


def make_razorpayx_property_setters():
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


def make_razorpayx_workflows():
    make_workflows(WORKFLOWS)


################### Before Uninstall Setup ###################
def delete_razorpayx_custom_fields():
    delete_custom_fields(CUSTOM_FIELDS)


def delete_razorpayx_property_setters():
    delete_property_setters(PROPERTY_SETTERS)


def delete_razorpayx_role_and_permissions():
    # TODO
    delete_role_and_permissions(ROLES)


def delete_razorpayx_workflows():
    # TODO
    delete_workflows(WORKFLOWS)
