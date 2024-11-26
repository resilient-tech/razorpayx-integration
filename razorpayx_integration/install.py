import click

from razorpayx_integration.constants import BUG_REPORT_URL
from razorpayx_integration.hooks import app_title as APP_NAME
from razorpayx_integration.setup import (
    make_custom_fields,
    make_property_setters,
    make_role_and_permissions,
)


def after_install():
    try:
        make_custom_fields()
        make_property_setters()
        make_role_and_permissions()

    except Exception as e:
        click.secho(
            (
                f"\nInstallation of {APP_NAME} failed due to an error."
                "Please try re-installing the app or "
                f"report the issue on {BUG_REPORT_URL} if not resolved."
            ),
            fg="bright_red",
        )
        raise e

    click.secho(f"\nThank you for installing {APP_NAME}!", fg="green")
