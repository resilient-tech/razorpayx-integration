import click

from razorpayx_integration.constants import BUG_REPORT_URL
from razorpayx_integration.hooks import app_title as APP_NAME
from razorpayx_integration.setup import (
    delete_custom_fields,
    delete_property_setters,
    delete_role_and_permissions,
    delete_workflow,
)


def before_uninstall():
    try:
        delete_custom_fields()
        delete_property_setters()
        delete_role_and_permissions()
        delete_workflow()
    except Exception as e:
        click.secho(
            (
                f"\nUninstallation of {APP_NAME} failed due to an error."
                "Please try re-uninstalling the app or "
                f"report the issue on {BUG_REPORT_URL} if not resolved."
            ),
            fg="bright_red",
        )
        raise e

    click.secho(f"\nThank you for using {APP_NAME}!", fg="green")
