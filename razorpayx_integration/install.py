import click
import frappe

from razorpayx_integration.constants import BUG_REPORT_URL, PAYMENTS_PROCESSOR_APP
from razorpayx_integration.hooks import app_title as APP_NAME
from razorpayx_integration.setup import (
    create_payments_processor_custom_fields,
    setup_customizations,
)

POST_INSTALL_PATCHES = []


def after_install():
    try:
        setup_customizations()
        run_post_install_patches()

    except Exception as e:
        click.secho(
            (
                f"Installation of {APP_NAME} failed due to an error. "
                "Please try re-installing the app or "
                f"report the issue on {BUG_REPORT_URL} if not resolved."
            ),
            fg="bright_red",
        )
        raise e

    click.secho(f"Thank you for installing {APP_NAME}!!\n", fg="green")


def run_post_install_patches():
    if not POST_INSTALL_PATCHES:
        return

    click.secho("Running post-install patches...", fg="yellow")

    if not frappe.db.exists("Company", {"country": "India"}):
        return

    frappe.flags.in_patch = True

    try:
        for patch in POST_INSTALL_PATCHES:
            patch_module = f"razorpayx_integration.patches.post_install.{patch}.execute"
            frappe.get_attr(patch_module)()

    finally:
        frappe.flags.in_patch = False


def after_app_install(app_name):
    if app_name == PAYMENTS_PROCESSOR_APP:
        create_payments_processor_custom_fields()
