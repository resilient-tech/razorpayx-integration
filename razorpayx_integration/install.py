import click
import frappe

from razorpayx_integration.hooks import app_title as APP_NAME
from razorpayx_integration.razorpayx_integration.constants import BUG_REPORT_URL
from razorpayx_integration.setup import (
    make_custom_fields,
    make_property_setters,
    make_roles_and_permissions,
    make_workflows,
)

POST_INSTALL_PATCHES = ("set_default_razorpayx_payment_mode",)


def after_install():
    try:
        make_custom_fields()
        make_property_setters()
        make_roles_and_permissions()
        make_workflows()

    except Exception as e:
        click.secho(
            (
                f"\nInstallation of {APP_NAME} failed due to an error. "
                "Please try re-installing the app or "
                f"report the issue on {BUG_REPORT_URL} if not resolved."
            ),
            fg="bright_red",
        )
        raise e

    click.secho(f"\nThank you for installing {APP_NAME}!", fg="green")


def run_post_install_patches():
    click.secho(f"\nRunning post-install patches for {APP_NAME}...", fg="yellow")

    if not frappe.db.exists("Company", {"country": "India"}):
        return

    frappe.flags.in_patch = True

    try:
        for patch in POST_INSTALL_PATCHES:
            patch_module = f"razorpayx_integration.patches.post_install.{patch}.execute"
            frappe.get_attr(patch_module)()

    finally:
        frappe.flags.in_patch = False
