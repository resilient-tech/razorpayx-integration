import click

import frappe

from razorpayx_integration.constant import BUG_REPORT_URL

POST_INSTALL_PATCHES = (
    "setup_custom_fields",
    "setup_property_setters",
)


def after_install():
    try:
        click.secho("Patching...", fg="blue")
        run_post_install_patches()

    except Exception as e:
        click.secho(
            (
                "Installation for RazorPayX Integration failed due to an error."
                "Please try re-installing the app or"
                f"report the issue on {BUG_REPORT_URL} if not resolved."
            ),
            fg="bright_red",
        )
        raise e

    click.secho("Thank you for installing RazorPayX Integration!", fg="green")


def run_post_install_patches():
    frappe.flags.in_patch = True

    try:
        for patch in POST_INSTALL_PATCHES:
            frappe.get_attr(
                f"razorpayx_integration.patches.post_install.{patch}.execute"
            )()

    finally:
        frappe.flags.in_patch = False
