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
    click.secho(f"\nCreating Roles and Permissions for {APP_NAME}...", fg="blue")

    make_payment_utils_roles_and_permissions()
    make_razorpayx_roles_and_permissions()


def make_custom_fields():
    click.secho(f"\nCreating Custom Fields for {APP_NAME}...", fg="blue")

    make_payment_utils_custom_fields()
    make_razorpayx_custom_fields()


def make_property_setters():
    click.secho(f"\nCreating Property Setters for {APP_NAME}...", fg="blue")

    make_payment_utils_property_setters()
    make_razorpayx_property_setters()


def make_workflows():
    click.secho(f"\nCreating Workflows for {APP_NAME}...", fg="blue")

    make_payment_utils_workflows()
    make_razorpayx_workflows()


##### Before Uninstall Setup #####
def delete_customizations():
    delete_workflows()
    delete_custom_fields()
    delete_property_setters()
    delete_role_and_permissions()


def delete_custom_fields():
    click.secho(f"\nDeleting Custom Fields of {APP_NAME}...", fg="blue")

    delete_razorpayx_custom_fields()
    delete_payment_utils_custom_fields()


def delete_property_setters():
    click.secho(f"\nDeleting Property Setters off {APP_NAME}...", fg="blue")

    delete_razorpayx_property_setters()
    delete_payment_utils_property_setters()


def delete_workflows():
    click.secho(f"\nDeleting Workflows of {APP_NAME}...", fg="blue")

    delete_razorpayx_workflows()
    delete_payment_utils_workflows()


def delete_role_and_permissions():
    click.secho(f"\nDeleting Roles and Permissions of {APP_NAME}...", fg="blue")

    delete_razorpayx_role_and_permissions()
    delete_payment_utils_role_and_permissions()
