import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import (
    create_custom_fields as make_custom_fields,
)
from payment_integration_utils.payment_integration_utils.setup import (
    delete_custom_fields,
    delete_property_setters,
    delete_roles_and_permissions,
    make_roles_and_permissions,
)

from razorpayx_integration.constants import PAYMENTS_PROCESSOR_APP
from razorpayx_integration.razorpayx_integration.constants.custom_fields import (
    CUSTOM_FIELDS,
    PROCESSOR_FIELDS,
)
from razorpayx_integration.razorpayx_integration.constants.property_setters import (
    PROPERTY_SETTERS,
)
from razorpayx_integration.razorpayx_integration.constants.roles import ROLES


################### After Install ###################
def setup_customizations():
    click.secho("Creating Roles and Permissions...", fg="blue")
    create_roles_and_permissions()

    click.secho("Creating Custom Fields...", fg="blue")
    create_custom_fields()

    if PAYMENTS_PROCESSOR_APP in frappe.get_installed_apps():
        click.secho(
            f"Creating Custom Fields for {frappe.unscrub(PAYMENTS_PROCESSOR_APP)}...",
            fg="blue",
        )
        create_payments_processor_custom_fields()

    click.secho("Creating Property Setters...", fg="blue")
    create_property_setters()


# Note: separate functions are required to use in patches
def create_roles_and_permissions():
    make_roles_and_permissions(ROLES)


def create_custom_fields():
    make_custom_fields(CUSTOM_FIELDS)


def create_property_setters():
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


def create_payments_processor_custom_fields():
    make_custom_fields(PROCESSOR_FIELDS)


################### Before Uninstall ###################
def delete_customizations():
    click.secho("Deleting Custom Fields...", fg="blue")
    delete_custom_fields(CUSTOM_FIELDS)

    click.secho(
        f"Deleting Custom Fields for {frappe.unscrub(PAYMENTS_PROCESSOR_APP)}...",
        fg="blue",
    )
    delete_payments_processor_custom_fields()

    click.secho("Deleting Property Setters...", fg="blue")
    delete_property_setters(PROPERTY_SETTERS)

    click.secho("Deleting Roles and Permissions...", fg="blue")
    delete_roles_and_permissions(ROLES)


# Note: separate functions are required to use in patches
def delete_payments_processor_custom_fields():
    delete_custom_fields(PROCESSOR_FIELDS)
