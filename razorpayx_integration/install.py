import click

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import (
    add_permission,
    setup_custom_perms,
    update_permission_property,
)

from razorpayx_integration.constant import BUG_REPORT_URL, RAZORPAYX_SETTING_DOCTYPE

# todo: some custom fields are remain to add
CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "insert_after": "currency",
        },
    ],
}

# todo: some property setters are remain to add
PROPERTY_SETTERS = [
    {
        "doctype_or_docfield": "DocField",
        "doctype": "Bank Transaction",
        "fieldname": "transaction_id",
        "property": "hidden",
        "value": 1,
        "property_type": "Check",
    },
    {
        "doctype_or_docfield": "DocField",
        "doctype": "Bank Transaction",
        "fieldname": "transaction_id",
        "property": "print_hide",
        "value": 1,
        "property_type": "Check",
    },
]


def after_install():
    try:
        click.secho("Patching...", fg="blue")
        make_custom_fields()
        make_property_setters()
        make_role_and_permissions()

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


def make_custom_fields():
    create_custom_fields(CUSTOM_FIELDS)


def make_property_setters():
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


# todo: custom fields and property setters have to set for the role (permissions)
def make_role_and_permissions():
    role_name = "RazorPayX Integration Manager"

    try:
        role = frappe.new_doc("Role")
        role.update(
            {
                "role_name": role_name,
                "desk_access": 1,
            }
        )
        role.save()
    except frappe.DuplicateEntryError:
        pass

    frappe.reload_doc(
        "razorpayx_integration", "doctype", "razorpayx_integration_setting"
    )
    setup_custom_perms(RAZORPAYX_SETTING_DOCTYPE)

    for doctype in ("Employee", "Customer", "Supplier", "Payment Entry"):
        add_permission(doctype, role_name, 7)
        update_permission_property(doctype, role_name, 7, "write", 1)
