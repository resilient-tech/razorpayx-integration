"""
⚠️ Notes:
- Always first customize the `Payment Utils` and then other Integrations.
- Always first delete the other Integrations and then `Payment Utils`.

"""

import click

from razorpayx_integration.hooks import app_title as APP_NAME
from razorpayx_integration.payment_utils.setup import *
from razorpayx_integration.razorpayx_integration.setup import *


##### After Install Setup #####
def setup_customizations():
    make_roles_and_permissions()
    make_custom_fields()
    make_property_setters()
    make_workflows()


def make_roles_and_permissions():
    click.secho("Creating Roles and Permissions...", fg="blue")

    make_payment_utils_roles_and_permissions()
    make_razorpayx_roles_and_permissions()


def make_custom_fields():
    click.secho("Creating Custom Fields...", fg="blue")

    make_payment_utils_custom_fields()
    make_razorpayx_custom_fields()


def make_property_setters():
    click.secho("Creating Property Setters...", fg="blue")

    make_payment_utils_property_setters()
    make_razorpayx_property_setters()


def make_workflows():
    click.secho("Creating Workflows...", fg="blue")

    make_payment_utils_workflows()
    make_razorpayx_workflows()


##### Before Uninstall Setup #####
def delete_customizations():
    delete_custom_fields()
    delete_property_setters()
    delete_roles_and_permissions()


def delete_custom_fields():
    click.secho("Deleting Custom Fields...", fg="blue")

    delete_razorpayx_custom_fields()
    delete_payment_utils_custom_fields()


def delete_property_setters():
    click.secho("Deleting Property Setters...", fg="blue")

    delete_razorpayx_property_setters()
    delete_payment_utils_property_setters()


def delete_roles_and_permissions():
    click.secho("Deleting Roles and Permissions...", fg="blue")

    delete_razorpayx_role_and_permissions()
    delete_payment_utils_role_and_permissions()
